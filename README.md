# Pipeline Audit Dashboard

An interactive HTML dashboard for tracking row counts through a Python data pipeline and comparing results across runs.

**This repository is a synthetic demonstration.** All sample counts, dates, identifiers, paths, filenames, and processing rules are invented. No production datasets or employee records are included.

The example contains **two runs with 17 audit events per run**, illustrating increases, decreases, and unchanged counts.

## Interactive Demo

**[Open the live dashboard](https://linyuli303.github.io/DataEngineeringAuditLog/)**

Explore side-by-side run comparisons, synchronized scrolling, matching-step highlighting, and row-count changes. No download or Python installation is required to explore the live demo.

### Video Walkthroughs

https://github.com/user-attachments/assets/1a80eb82-f665-449c-952a-1ab0ff951df4

https://github.com/user-attachments/assets/f647e60a-fcee-4030-93c9-ecc6d1592343

https://github.com/user-attachments/assets/99ab5401-b56e-46e2-8a95-40c6eac3346e

https://github.com/user-attachments/assets/922b3516-0319-4d35-ad94-57c92570bfc2

## Why This Dashboard?

Source files can be replaced between processing runs, while intermediate DataFrames may be filtered, joined, expanded, or overwritten.

This dashboard illustrates how checkpoint metadata can preserve a history of those changes and help answer:

- How many rows were read from each source?
- How did filters and mapping rules affect the dataset?
- Which checkpoints changed compared with the preceding run?
- What was the final dataset size?

The audit records **dataset-level counts**, not individual data records.

## Features

- **Persistent audit history:** checkpoint metadata is stored in a CSV, separate from source files.
- **Side-by-side comparison:** inspect the latest two recorded runs.
- **Signed deltas:** positive and negative changes are highlighted in Yamabuki gold; `0` means unchanged; `—` means no comparable earlier count is available.
- **Synchronized scrolling:** scroll either comparison table to move both; paired row heights keep checkpoints aligned.
- **Matching-step selection:** click a row to highlight the same checkpoint in both runs. Click again or press Escape to clear. Keyboard selection supports Enter and Space.
- **Separate content tabs:** comparison, current-run details, workflow, and history each have their own panel.
- **Source-path tooltips:** hover over a source-read checkpoint name to reveal its synthetic source path.
- **Mermaid workflow:** visualize the demonstration pipeline.
- **Japanese-inspired theme:** indigo, ivory, gold, and lavender colors inspired by [Japanese Color Atlas](https://japanesecoloratlas.com/).

On narrow screens, comparison panels stack vertically.

## Dashboard Sections

| Tab | Content |
| --- | --- |
| **Compare latest 2 runs** | Side-by-side checkpoint counts and deltas |
| **Current run** | Summary cards and current-run audit events |
| **Workflow** | Mermaid diagram of the demonstration pipeline |
| **Run history** | Expandable logs of retained runs |

## Understanding the Audit

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

**Counts describe successive snapshots. They should not be summed across pipeline stages.**

### Delta Definition

```text
Delta = this run's count − the same checkpoint's count in the preceding recorded run
```

Checkpoint matching uses event type, stage label, and DataFrame name.

| Display | Interpretation |
| --- | --- |
| `+120` | 120 more rows than the preceding run |
| `-25` | 25 fewer rows |
| `0` | No change |
| `—` | No comparable earlier checkpoint or no numerical count |

The previous-run panel compares against its own predecessor—not the latest run. Since this demo contains only two runs, the older panel has no preceding run and displays dashes.

### Example Results

| Checkpoint | Previous run | Latest run | Change |
| --- | ---: | ---: | ---: |
| Current source | 12,400 | 12,520 | +120 |
| Eligible source records | 3,850 | 3,825 | -25 |
| Target reference | 28 | 28 | 0 |
| Final dataset | 6,800 | 6,840 | +40 |

## Repository Contents

| File | Purpose |
| --- | --- |
| `index.html` | Live dashboard entry page |
| `demo_dashboard.html` | Pre-generated dashboard |
| `demo_audit_history.csv` | Two synthetic audit runs |
| `pipeline_audit_demo.py` | Audit logging and HTML-generation helper |
| `generate_demo.py` | Synthetic demonstration generator |
| `pipeline_audit_demo.ipynb` | Notebook demonstration |
| `requirements.txt` | Python dependencies |
| `DESCRIPTION.txt` | Short project description |

## Scope and Limitations

- The dashboard is a generated snapshot, not a live monitoring service.
- Audit timestamps describe Python checkpoints, not Power BI refresh times.
- Row-count changes indicate differences in dataset size; they do not explain every underlying data change.
- Audit history preserves metadata, not previous source-file contents.
- Synchronized row alignment assumes the runs use the same checkpoint order.
- The Mermaid diagram requires internet access. Other dashboard interactions work offline when viewing the saved HTML.

## Synthetic Data and Privacy

All records in this demonstration are invented, including paths such as `C:/demo/input/`.

No actual source workbooks, employee-level records, or production audit histories are included.

Source paths displayed through tooltips are still present in the HTML and CSV. Hover-only presentation is a visual choice, not a security control.


