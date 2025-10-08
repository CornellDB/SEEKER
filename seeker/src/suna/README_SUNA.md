# Suna Integration Overview

This package brings the Suna confounder discovery algorithm into SEEKER’s service architecture. It mirrors the layout of other features (e.g., `qgram_index`) and exposes a service API for the interpreter, scripts, and notebooks.

## Module Layout
- `__init__.py` — Re-exports configs, services, and result dataclasses for convenient imports.
- `config.py` — Dataclasses (`SunaConfig`, `BootstrapConfig`, `SketchConfig`) plus CLI parsing helpers. Supports metadata-driven defaults with override hooks.
- `encoders.py` — Lightweight categorical encoder utilities and helpers for selecting candidate covariates.
- `sketches.py` — Sketch preparation and caching helpers. Currently materializes single-table sketches but keeps cache management aligned with the paper’s design.
- `scoring.py` — Bivariate causal discovery scoring (bootstrap MI deltas) and stubs for optional subspace methods.
- `discovery.py` — Iterative Algorithm 1 loop that selects confounders based on bootstrap quantiles and MI-drop heuristics; produces typed results.
- `pipelines.py` — High-level orchestration that wires preprocessing, discovery, and caching for a `DatasetModel`.
- `results.py` — Dataclasses describing findings, bootstrap summaries, and overall discovery results.
- `service.py` — SEEKER-facing service + `SunaDataSeeker` adapter used by the interpreter and scripts.

## Usage

### Interpreter Command
Add the operation to a query plan:
```
suna_discover:dataset=<name>:treatment=<col>:outcome=<col>:candidate_covariates=Z1,Z2
```
- `dataset` (required): key from the loaded dataset models.
- `treatment`, `outcome`: required if metadata lacks `suna.treatment_column` / `suna.outcome_column`.
- Optional overrides include `method`, `candidate_covariates`, `tau`, `bootstrap.n_samples`, `sketch.enable_cache=false`, etc.
Results print in the terminal and, when available, render via `SearchResultsVisualizer`.

### Script
Execute the helper script to run discovery offline:
```bash
python -m seeker.src.scripts.run_suna_discovery \
  --dataset my_dataset \
  --tau 0.1 \
  --n-samples 200
```
The script reads metadata from `dataset_examples/<dataset>.json`, stores discovery reports under `dist/suna/`, and echoes findings to stdout.

## Metadata Schema
Annotate datasets with an optional `suna` block:
```json
{
  "suna": {
    "treatment_column": "T",
    "outcome_column": "O",
    "candidate_covariates": ["Z1", "Z2"],
    "join_keys": [["user_id"]],
    "tau": 0.05,
    "n_boot": 100,
    "default_method": "bcd"
  }
}
```
Overrides supplied via CLI/interpreter take precedence.

### Synthetic Demo Dataset

The Suna prototype relied on synthetic data with known confounders.  The SEEKER
integration now ships an equivalent generator in `seeker.src.suna.synthetic`.
Run discovery against the synthetic asset the same way you would target any
other dataset:

```bash
python -m seeker.src.scripts.run_suna_discovery \
  --dataset suna_synthetic \
  --generate-synthetic \
  --tau 0.05
```

- The first invocation materializes `dataset_examples/suna_synthetic.csv` and
  `dataset_examples/suna_synthetic_metadata.json`.  Subsequent runs reuse the
  files unless `--generate-synthetic` is specified.
- Use `--synthetic-samples <n>` and `--synthetic-seed <seed>` to customise the
  number of rows or the RNG seed while still producing metadata that matches the
  SEEKER ingestion contract.
- Columns cover treatment, outcome, two true confounders, an instrumental
  variable, a proxy, seasonal and trend terms, plus noise—mirroring the
  structure of the prototype experiments.
- Metadata for the synthetic dataset already declares the treatment, outcome,
  candidate covariates, and bootstrap defaults under the `suna` block so the CLI
  requires no extra overrides.

## Follow-Up Ideas
- Expand `sketches.py` to build semi-ring sketches across relational joins once SEEKER exposes join graphs.
- Replace the MI-drop heuristic with a proper conditional MI estimator from the Suna prototype.
- Wire optional extensions (`subgroup`, `mprp`, `shap`) once corresponding extras are packaged.
