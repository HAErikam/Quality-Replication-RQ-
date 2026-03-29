"""Cliente de acceso al modelo LLM con respuesta JSON y metadatos de uso."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI


for ruta in [
    Path.cwd() / ".env",
    Path(__file__).resolve().parents[2] / ".env",
    Path(__file__).resolve().parents[3] / ".env",
]:
    if ruta.exists():
        load_dotenv(dotenv_path=ruta, override=False)
        print(f"[DEBUG] .env cargado desde: {ruta}")
        break
else:
    print("[DEBUG] No se encontró archivo .env")


@dataclass
class LLMUsage:
    """
    Estructura simple para registrar uso del modelo.
    Compatible con el pipeline.
    """
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: str = ""

    def as_dict(self) -> dict:
        """
        Devuelve el uso como diccionario.
        """
        return asdict(self)


class OpenAIJsonClient:
    """
    Cliente para invocar el modelo y recuperar respuesta JSON.
    Compatible con pipeline.py.
    """

    def __init__(self, model: str = "gpt-5.1", temperature: float = 0.2) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        print("[DEBUG] OPENAI_API_KEY detectada:", bool(api_key))

        if not api_key:
            raise RuntimeError(
                "Falta OPENAI_API_KEY. Verifique el archivo .env o defina la variable en la terminal."
            )

        self.model = model
        self.temperature = temperature
        self.client = OpenAI(api_key=api_key)

    def call_json(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
    ) -> tuple[Dict[str, Any], LLMUsage]:
        input_messages = []

        if system_prompt:
            input_messages.append({"role": "system", "content": system_prompt})

        input_messages.append({"role": "user", "content": user_prompt})

        response = self.client.responses.create(
            model=self.model,
            temperature=self.temperature,
            input=input_messages,
            text={"format": {"type": "json_object"}},
        )

        texto = getattr(response, "output_text", None)
        if not texto:
            raise RuntimeError("La respuesta del modelo no devolvió texto JSON.")

        data = json.loads(texto)

        usage_raw = getattr(response, "usage", None)
        usage = LLMUsage()

        if usage_raw is not None:
            usage.prompt_tokens = getattr(usage_raw, "input_tokens", 0) or 0
            usage.completion_tokens = getattr(usage_raw, "output_tokens", 0) or 0
            usage.total_tokens = getattr(usage_raw, "total_tokens", 0) or (
                usage.prompt_tokens + usage.completion_tokens
            )
            usage.cost_usd = ""

        return data, usage