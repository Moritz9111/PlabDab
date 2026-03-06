# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PLAbDab (Patent and Literature Antibody Database) is a local Streamlit application for exploring antibody sequence and structure data. The project uses data downloaded from public sources (NCBI/patent databases) including paired/unpaired antibody sequences and predicted 3D structure models.

## Running the App

```bash
streamlit run plabdab_app.py
```

## Dependencies

- Python 3
- `streamlit` — web UI framework
- `pandas` — data loading and manipulation

No `requirements.txt` exists yet; dependencies must be installed manually (`pip install streamlit pandas`).

## Architecture

- **`plabdab_app.py`** — Single-file Streamlit app. Entry point for the entire application.
- **`data-dev/`** — Local data directory (not committed to version control). Contains:
  - `paired_sequences_2024-08-28.csv.gz` — Compressed CSV of paired antibody sequences (heavy + light chain)
  - `unpaired_sequences*.csv.gz` — Unpaired antibody sequences
  - `failed_to_pair.csv.gz` — Sequences that failed pairing
  - `models/` — ~65k PDB structure files (antibody 3D models)
  - `kasearch_db/` — KA-Search database files (Heavy, Light, Mix chains + metadata)
  - `chunks/` — Intermediate CSV splits from data download pipeline
  - `stats/` — Precomputed visualizations (SVG plots)
  - `config.json` — NCBI query config (keywords, sequence length filter, last update date)
  - `log.txt` — Download pipeline log

## Data Schema (paired_sequences CSV)

Key columns: `ID`, `heavy_sequence`, `light_sequence`, `heavy_definition`, `light_definition`, `organism`, `reference_authors`, `reference_title`, `update_date`, `cdr_lengths`, `model`, `pairing`, `targets_mentioned`

- `targets_mentioned` — semicolon-separated antigen/target names (e.g. `"EGFR; ERBB; ERBB1"`). ~28% of rows are empty.
- `model` — PDB model ID or `"FAILED"`. Corresponding `.pdb` files in `models/`.
- ~173k rows total.

## Key Details

- Data paths use `Path(__file__).parent / "data-dev"` (relative to script location).
- The `data-dev/` directory is large (~130MB+ compressed) and should not be committed.
- This is not a git repository yet.
