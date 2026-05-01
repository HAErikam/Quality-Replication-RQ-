# INVEST Experimental Package: Evaluation, Improvement, and Reevaluation of User Stories with GPT-5.1
 
This package provides an experimental implementation of a 3-phase INVEST protocol, preserving the complete protocol, methodological traceability, and the statistical analysis artifacts associated with this project.

## Research Context
This repository is referenced in the Data Availability Statement of the associated manuscript:
"Assessing and Improving the Quality of User Stories Using Large Language Models: A Replication Study in an Industrial Context"  and provides the experimental artifacts required to understand and partially reproduce the methodology.

## Structure

```text
Quality-Replication-RQ/
├── .env (no disponible, se debe crear)
├── README.md
├── requirements.txt
├── run_pipeline.py
└── invest_protocol/
    ├── __init__.py
    ├── cli.py
    ├── constants.py
    ├── pipeline.py
    ├── core/
    │   ├── openai_client.py
    │   └── prompts.py
    ├── io/
    │   └── excel_io.py
    ├── protocols/
    │   ├── loader.py
    │   └── protocolo_invest_completo.txt
    └── utils/
        └── helpers.py
```

## Description

1. **Responsibilities**:
   - `pipeline.py`: orchestrates the 3 phases of the protocol.
   - `prompts.py`: builds the prompts used in each phase.
   - `openai_client.py`: centralizes model calls and usage metrics.
   - `excel_io.py`: manages reading and writing the experimental Excel file.
   - `loader.py`: loads the protocol from an external reusable file.

2. **Reusable protocol**:  
   The full protocol is stored in `protocols/protocolo_invest_completo.txt`, so it can be invoked from other scripts, interfaces, or tests.

3. **Comments**:  
   The code includes comments in Spanish to explain clearly what each part does and why it is performed.

4. **Experimental replicability**:  
   The following elements are preserved:
   - the complete 3-phase workflow,
   - six complete runs of the full 3-phase cycle,
   - Excel export with 4 sheets,
   - `meta.json` export,
   - token usage metrics,
   - reinforced rules for incident handling.

## Reproducibility Scope

This package supports:
- methodological reproducibility (protocol),
- computational reproducibility (pipeline execution),
- analytical reproducibility (statistical outputs),

but does not enable full data-level replication due to confidentiality constraints, as original user-story data cannot be disclosed.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Execution settings are specified in the Model Configuration section to ensure controlled and reproducible execution.

> Execution incurs a USD cost for each model call in all three phases for each full run per user story.

Create a `.env` file with:

```bash
OPENAI_API_KEY=sk-...
```
This information should not be included in any repository. It is recommended to add the corresponding restriction to `.gitignore`.

## Model Configuration

These settings correspond to the configuration reported in the manuscript:

- Execution environment: programmatic execution (API-based)
- Model: gpt-5.1 (API-based)
- Temperature: 0.2
- Runs: 6 per story (full 3-phase cycle)

## Quick Start

To reproduce the experiment:

1. Prepare an anonymized input Excel file
2. Configure your API key in `.env`
3. Run the pipeline using one of the options below
   
## Running from Python

```python
from invest_protocol.pipeline import ejecutar_pipeline_invest_excel

meta = ejecutar_pipeline_invest_excel(
    ruta_excel_entrada="historias_entrada.xlsx",
    runs_fase1=6,
    model="gpt-5.1",
    temperature=0.2,
    usar_corrida_base_f2_f3=1,  # conservado por compatibilidad
)
print(meta)
```

## Running from the terminal

```bash
python -m invest_protocol.cli historias_entrada.xlsx --runs-fase1 6 --model gpt-5.1 --temperature 0.2 --corrida-base-f2-f3 1
```

## Expected input format

Input data must be anonymized in advance and must not contain real data from people, databases, or infrastructure elements. This is essential for security reasons when using industrial-context data. This anonymization process is not included here; the information is generated and stored only in a local environment. Likewise, the changes made should not be publicly shared in any repository.

The `Entrada` sheet must contain exactly the following columns:

- `ID`
- `Estado de tarea`
- `Título`
- `Descripción`
- `Proyecto`
- `Criterios de aceptación`

## Generated outputs

- One `.xlsx` file with the following sheets:
  - `Entrada`
  - `Evaluada`
  - `Mejorada`
  - `Reevaluada`

- One `*.meta.json` file with run information:
  - `ID_corrida`
  - `fecha_corrida_utc`
  - `modelo`
  - `temperature`

These metadata fields are preserved for traceability and transparency in the `Evaluada`, `Mejorada`, and `Reevaluada` sheets.

## Technical notes

- In this version, each run executes the full cycle: Phase 1 evaluation, Phase 2 improvement, and Phase 3 reevaluation. Therefore, `ID_corrida` consistently identifies the complete cycle that produced each row in `Evaluada`, `Mejorada`, and `Reevaluada`.

- The parameter `usar_corrida_base_f2_f3` is preserved only for backward compatibility with previous integrations, but it no longer changes the execution flow.

- Detected incidents are not converted into user stories during Phase 2. This only applies if such cases exist, as they may result from an incident being incorrectly recorded as a requirement. Although this should not be the norm in projects, the protocol explicitly handles and controls this scenario.

- If the model response in Phase 2 does not include valid `items`, the system uses a safe fallback mechanism to continue execution without interrupting the process.
  
## Limitations

Results produced using this package are specific to the dataset and experimental conditions of the study.

Reproducibility is limited by:
- absence of original user stories (confidentiality),
- potential changes in the underlying model over time,
- dependency on external API behavior.

Therefore, results should not be generalized without further validation.

## Methodological value of the statistical files

Including these files in the experimental package improves:

- process **transparency**,
- and the study’s **methodological replicability**.

These artifacts allow other researchers to review:

- whether the protocol produces measurable improvements,
- in which criteria agreement is stronger,
- and where interpretation differences still remain.

## Important Note

Original user stories are not included due to confidentiality constraints.

Any additional data derived from industrial contexts should be handled according to applicable confidentiality and data protection requirements.

## Citation

Full reference will be added after publication.

Preprint or accepted version will be linked here when available.
