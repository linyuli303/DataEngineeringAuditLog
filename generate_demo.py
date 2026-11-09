"""Build a public demo from fully invented audit records.
Run: python generate_demo.py
This overwrites ONLY demo_audit_history.csv and demo_dashboard.html.
It never reads Excel, production history, or private notebooks.
"""
import csv
import webbrowser
from datetime import datetime, timedelta, timezone
from uuid import uuid5, NAMESPACE_URL
import pipeline_audit_demo as audit


def build_demo(open_browser=False):
    # 17 events per run: start + 4 source reads + 11 checkpoints + completion.
    stages = [
        ("SOURCE_READ", "Read target reference", "df_targets", 28, 28, 6, "targets.xlsx", "Targets"),
        ("SOURCE_READ", "Read reference mapping", "df_mapping", 64, 64, 5, "reference_mapping.xlsx", "Mapping"),
        ("SOURCE_READ", "Read current source", "df_source", 12400, 12520, 12, "current_source.xlsx", "Data"),
        ("SOURCE_READ", "Read historical source", "df_history", 2100, 2100, 12, "historical_source.xlsx", "Data"),
        ("DATAFRAME", "Combine current and historical records", "df_combined", 14500, 14620, 12, "", ""),
        ("DATAFRAME", "Keep records matching reference mapping", "df_filtered", 4620, 4700, 14, "", ""),
        ("DATAFRAME", "Remove invalid and duplicate mapping entries", "df_mapping_clean", 60, 60, 5, "", ""),
        ("DATAFRAME", "Enrich matched records with reference mapping", "df_enriched", 4620, 4700, 16, "", ""),
        ("DATAFRAME", "Deduplicate entity records", "df_entities", 600, 610, 4, "", ""),
        ("DATAFRAME", "Keep targets with valid categories", "df_targets_clean", 26, 26, 6, "", ""),
        ("DATAFRAME", "Expand entities against category-specific targets", "df_expanded", 7200, 7320, 10, "", ""),
        ("DATAFRAME", "Keep eligible source records", "df_eligible", 3850, 3825, 16, "", ""),
        ("DATAFRAME", "Combine eligible records and generated targets", "df_combined_output", 11050, 11145, 10, "", ""),
        ("DATAFRAME", "Remove superseded records", "df_deduplicated", 11000, 11090, 10, "", ""),
        ("DATAFRAME", "Final dataset after exclusion rule", "df_final", 6800, 6840, 10, "", ""),
    ]
    records = []
    for index in range(2):
        run_id = str(uuid5(NAMESPACE_URL, "synthetic-pipeline-demo-run-" + str(index)))
        start = datetime(2025, 1, 6 + index * 7, 9, 0, tzinfo=timezone.utc)
        def event(sequence, event_type, stage, dataframe="", rows="", columns="", filename="", worksheet=""):
            record = dict.fromkeys(audit.AUDIT_FIELDS, "")
            record.update(run_id=run_id, sequence=sequence,
                timestamp_utc=(start + timedelta(seconds=sequence * 2)).isoformat(),
                event_type=event_type, stage=stage, dataframe=dataframe,
                row_count=rows, column_count=columns, worksheet=worksheet)
            if filename:
                # Invented path for hover demonstration only; files do not exist.
                record["source_path"] = "C:/demo/input/" + filename
                record["read_started_at_utc"] = (start + timedelta(seconds=sequence * 2 - 1)).isoformat()
            return record
        records.append(event(1, "RUN_STARTED", "Demo pipeline started"))
        for sequence, (kind, stage, df, previous, latest, columns, filename, worksheet) in enumerate(stages, 2):
            records.append(event(sequence, kind, stage, df, previous if index == 0 else latest, columns, filename, worksheet))
        records.append(event(17, "RUN_COMPLETED", "Demo pipeline completed"))
    with audit.AUDIT_HISTORY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=audit.AUDIT_FIELDS)
        writer.writeheader()
        writer.writerows(records)
    audit.AUDIT_RUN = records[-1]["run_id"]
    audit._audit_dashboard()
    print("Built synthetic demo: 2 runs, 17 events each.")
    print("Open demo_dashboard.html in your browser.")
    if open_browser:
        webbrowser.open(audit.AUDIT_HTML.resolve().as_uri())
    return audit.AUDIT_HTML


if __name__ == "__main__":
    build_demo(open_browser=True)
