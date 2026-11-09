# Pipeline Audit Dashboard

An interactive HTML dashboard for tracking row counts through a Python data pipeline and comparing results across runs.

**This repository is a synthetic demonstration.** All sample counts, dates, identifiers, paths, filenames, and processing rules are invented. No production datasets or employee records are included.
The example contains **two runs with 17 audit events per run**, illustrating increases, decreases, and unchanged counts.

## Interactive Demo

[Open the live dashboard](https://linyuli303.github.io/DataEngineeringAuditLog/)

Explore side-by-side run comparisons, synchronized scrolling, matching-step highlighting, and row-count changes.

https://github.com/user-attachments/assets/1a80eb82-f665-449c-952a-1ab0ff951df4

https://github.com/user-attachments/assets/f647e60a-fcee-4030-93c9-ecc6d1592343

https://github.com/user-attachments/assets/99ab5401-b56e-46e2-8a95-40c6eac3346e

https://github.com/user-attachments/assets/922b3516-0319-4d35-ad94-57c92570bfc2

## Features

- **Persistent audit history:** checkpoint metadata is saved in a CSV, separate from source files.
- **Side-by-side comparison:** inspect the latest two recorded runs.
- **Signed deltas:** positive and negative changes are highlighted in Yamabuki gold; `0` means unchanged; `—` means there is no comparable earlier count.
- **Synchronized scrolling:** scroll either comparison table to move both; paired row heights keep checkpoints aligned.
- **Matching-step selection:** click a row to highlight the same checkpoint in both runs. Click again or press Escape to clear. Keyboard selection supports Enter and Space.
- **Exclusive tabs:** comparison, current-run details, workflow, and history each have a separate panel.
- **Source-path tooltips:** hover over a source-read checkpoint name to reveal its demonstration path.
- **Mermaid workflow:** visualize a generic transformation pipeline.
- **Japanese-inspired theme:** indigo, ivory, gold, and lavender colors inspired by Japanese Color Atlas (https://japanesecoloratlas.com/).

On narrow screens, comparison panels stack vertically.

## Repository contents

| File | Purpose |
| --- | --- |
| `demo_dashboard.html` | Pre-generated interactive dashboard |
| `demo_audit_history.csv` | Two fully synthetic audit runs |
| `pipeline_audit_demo.py` | Audit logging and HTML-generation helper |
| `generate_demo.py` | Builds the synthetic history and dashboard |
| `pipeline_audit_demo.ipynb` | Notebook entry point for generating the demo |
| `requirements.txt` | Python dependencies |
| `DESCRIPTION.txt` | Short description for the GitHub About field |

## Quick start

### View the existing dashboard

Open `demo_dashboard.html` in a modern browser.

The tables, tabs, comparison, scrolling, and selection features work offline. The Mermaid diagram requires internet access because its rendering library loads from jsDelivr.

### Regenerate the demo

Python **3.12 or later** is recommended.

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install dependencies and generate the dashboard:

```bash
pip install -r requirements.txt
python generate_demo.py
```

The generator saves `demo_audit_history.csv` and `demo_dashboard.html` beside the helper and attempts to open the dashboard in your default browser. Open the HTML file manually if necessary.

**Regenerating the demo overwrites these two demo output files.** It does not read Excel files, production audit histories, or private notebooks. This reset behavior is specific to the synthetic generator; the audit helper's logging functions append checkpoint records.

### Use the notebook

Keep `pipeline_audit_demo.ipynb`, `generate_demo.py`, and `pipeline_audit_demo.py` together. Open the notebook from that directory and run its cell.

A Jupyter-compatible environment is needed for the notebook; it is not included in `requirements.txt`.

## Reading the audit

Each event can contain:

| Field | Meaning |
| --- | --- |
| `run_id` | Identifier grouping events from one execution |
| `sequence` | Event order within the run |
| `timestamp_utc` | Time the checkpoint was recorded |
| `event_type` | Run marker, source read, or DataFrame checkpoint |
| `stage` | Human-readable checkpoint label |
| `dataframe` | Dataset name at that checkpoint |
| `row_count` | Number of rows at the checkpoint |
| `column_count` | Number of columns at the checkpoint |
| `source_path` | Input-file location, where applicable |
| `worksheet` | Excel worksheet, where applicable |
| `read_started_at_utc` | Source-read start time, where applicable |

The schema also reserves `metric_value` and `note` for optional metrics and context.

**Counts describe successive snapshots. Do not sum counts across pipeline stages.**

### Delta definition

```text
Delta = row count in this run − row count at the same checkpoint in the preceding recorded run
```

Checkpoint matching uses event type, stage label, and DataFrame name. Keep these identifiers consistent between runs.

- `+120`: 120 more rows than the preceding run.
- `-25`: 25 fewer rows.
- `0`: no change.
- `—`: no preceding comparable checkpoint, or no numerical count on the event.

The previous-run panel compares against its own predecessor, not the latest run. Because the demo supplies only two runs, the older panel has no earlier run and displays dashes.

## Adapt it to your own pipeline

1. Copy the helper into a **private** project and configure a private output directory.
2. Start audit initialization before processing.
3. Record source reads and meaningful checkpoints after filters, joins, deduplication, or other row-affecting rules.
4. Generate the HTML report after processing completes.
5. Preserve the history CSV between runs and keep it outside folders replaced by source uploads.

A report generated only at the end cannot recover intermediate DataFrames already overwritten. Checkpoints must be recorded while processing occurs.

For a real pipeline, use the loaded DataFrame in subsequent processing rather than reading the file independently again. The log describes Python checkpoints, not a Power BI refresh.

### Implementation limits

- The helper uses local CSV files and is intended for one writer at a time. Avoid concurrent pipeline runs writing to the same history file.
- Scroll alignment pairs rows by their position and assumes consistent checkpoint order. Matching-step highlighting uses checkpoint identity.
- The dashboard is a generated snapshot, not a live service. Regenerate the HTML after changing data or presentation code.
- If a helper is already imported into a notebook, replacing its file alone does not reload the module. Restart/reload it before regenerating the report.
- Audit history preserves metadata, not earlier source-file contents.
- Generated HTML includes client-side JavaScript; browser security policies may restrict some features.

## Privacy and publication

This demo was created from invented audit records, not production data with renamed people.

**Publish only the supplied demo files.** Do not add private source workbooks, real audit histories, organizational paths, or production notebook outputs to the repository.

Hover-only paths are **not hidden securely**: they remain in the HTML attributes and CSV. Demo paths point to nonexistent files under `C:/demo/input/`.

Review your changes and staged files before pushing. Remove sensitive notebook outputs before sharing, and avoid committing secrets or personal paths. If a secret has already been published, deleting it from the latest file alone does not remove it from Git history.

## Suggested GitHub description

Interactive Python pipeline-audit demo with persistent row-count history, side-by-side run comparison, synchronized scrolling, and synthetic data.

## License

No license has been selected in this template. Add an appropriate `LICENSE` file before presenting the project as licensed open-source software.

## Publishing this demo

The included `.gitignore` excludes common private inputs, workbooks, credential files, and Python caches. Only `demo_audit_history.csv` is allowed through the general CSV exclusion. Ignore rules do not protect files that are already tracked, do not remove secrets from Git history, and are not a substitute for reviewing staged files.

For an optional GitHub Pages demo, publish `main` from the repository root in Settings → Pages. `index.html` is a copy of the synthetic dashboard, and `.nojekyll` selects a plain static site. After regenerating the dashboard, refresh `index.html` from `demo_dashboard.html` before committing. GitHub Pages serves HTML; it does not execute this Python pipeline. Never publish real audit data to Pages.
