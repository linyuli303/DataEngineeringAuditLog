# Public demo helper — no production data or paths.
# Outputs are saved beside this module. Local file paths appear only on hover.
"""Original PIPELINE transformations with persistent checkpoint history and HTML.
Install: pip install pandas openpyxl
Run the entire script once per complete processing run.
"""
import csv
import os
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from html import escape
import pandas as pd
AUDIT_DIR = Path(__file__).resolve().parent
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_HISTORY = AUDIT_DIR / 'demo_audit_history.csv'
AUDIT_HTML = AUDIT_DIR / 'demo_dashboard.html'
AUDIT_RUN = str(uuid4())
AUDIT_SEQUENCE = 0
AUDIT_FIELDS = ['run_id', 'sequence', 'timestamp_utc', 'event_type', 'stage', 'dataframe', 'row_count', 'column_count', 'metric_value', 'source_path', 'worksheet', 'read_started_at_utc', 'note']

def _audit_now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')

def _audit_event(event_type, stage, dataframe='', row_count='', column_count='', metric_value='', source_path='', worksheet='', read_started_at_utc='', note=''):
    global AUDIT_SEQUENCE
    AUDIT_SEQUENCE += 1
    record = dict(zip(AUDIT_FIELDS, [AUDIT_RUN, AUDIT_SEQUENCE, _audit_now(), event_type, stage, dataframe, row_count, column_count, metric_value, str(source_path or ''), worksheet, read_started_at_utc, str(note)]))
    header = not AUDIT_HISTORY.exists() or AUDIT_HISTORY.stat().st_size == 0
    if not header:
        with AUDIT_HISTORY.open('r', newline='', encoding='utf-8') as handle:
            if next(csv.reader(handle), None) != AUDIT_FIELDS:
                raise RuntimeError('Audit schema mismatch. Archive the old pipeline audit CSV before running this version.')
    with AUDIT_HISTORY.open('a', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS)
        if header:
            writer.writeheader()
        writer.writerow(record)
        handle.flush()

def _audit_df(stage, name, value, note=''):
    if isinstance(value, pd.DataFrame):
        _audit_event('DATAFRAME', stage, dataframe=name, row_count=len(value), column_count=len(value.columns), note=note)

def _audit_read_excel(name, path, **kwargs):
    started = _audit_now()
    sheet = kwargs.get('sheet_name', 0)
    try:
        value = pd.read_excel(path, **kwargs)
    except Exception as exc:
        _audit_event('READ_ERROR', 'Read ' + name, dataframe=name, source_path=path, worksheet=sheet, read_started_at_utc=started, note=type(exc).__name__ + ': ' + str(exc))
        raise
    _audit_event('SOURCE_READ', 'Read ' + name, dataframe=name, row_count=len(value), column_count=len(value.columns), source_path=path, worksheet=sheet, read_started_at_utc=started)
    return value

def _audit_metric(label, value):
    _audit_event('METRIC', label, metric_value=int(value))

def _audit_dashboard():
    with AUDIT_HISTORY.open('r', newline='', encoding='utf-8') as handle:
        records = list(csv.DictReader(handle))
    current = [r for r in records if r['run_id'] == AUDIT_RUN]
    prior_ids = list(dict.fromkeys((r['run_id'] for r in records if r['run_id'] != AUDIT_RUN)))
    prior = [r for r in records if prior_ids and r['run_id'] == prior_ids[-1]]

    def esc(value):
        return escape(str(value), quote=True)

    def number(value):
        return f'{int(value):,}' if value != '' else '—'

    def key(r):
        return (r['event_type'], r['stage'], r['dataframe'])
    lookup = {key(r): r for r in prior}

    def table(items, compare=False):
        run_order = list(dict.fromkeys((r['run_id'] for r in records)))
        previous_run = {run_order[i]: run_order[i - 1] for i in range(1, len(run_order))}
        checkpoints = {(r['run_id'],) + key(r): r for r in records}
        rows = []
        for r in items:
            value = r['metric_value'] if r['event_type'] == 'METRIC' else r['row_count']
            old_id = previous_run.get(r['run_id'])
            old = checkpoints.get((old_id,) + key(r)) if old_id else None
            delta_html = '<span class="delta-unavailable" title="No comparable checkpoint in the previous run">—</span>'
            if old is not None:
                previous = old['metric_value'] if old['event_type'] == 'METRIC' else old['row_count']
                if value != '' and previous != '':
                    change = int(value) - int(previous)
                    delta_text = format(change, '+,') if change != 0 else '0'
                    delta_class = 'delta-change' if change != 0 else 'delta-zero'
                    title = 'Current ' + number(value) + ' − previous ' + number(previous)
                    delta_html = '<span class="' + delta_class + '" title="' + esc(title) + '">' + delta_text + '</span>'
            path_title = ' title="' + esc(r['source_path']) + '" tabindex="0"' if r['source_path'] else ''
            step_html = '<strong class="checkpoint-name"' + path_title + '>' + esc(r['stage']) + '</strong>'
            cls = 'bad' if r['event_type'] in ('READ_ERROR', 'RUN_FAILED') else ''
            cells = [esc(r['sequence']), step_html, esc(r['dataframe'] or '—'), esc(r['event_type']), number(value), number(r['column_count']), delta_html, esc(r['timestamp_utc'])]
            rows.append('<tr data-step="' + esc(str(key(r))) + '" class="' + cls + '">' + ''.join(('<td class="mono">' + value + '</td>' if i in (0, 2, 4, 5, 6, 7) else '<td>' + value + '</td>' for i, value in enumerate(cells))) + '</tr>')
        return '<div class="scroll"><table><thead><tr><th>#</th><th>Checkpoint</th><th>DataFrame</th><th>Type</th><th>Rows</th><th>Columns</th><th>Δ vs previous run</th><th>Timestamp · UTC</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
    final = [r for r in current if r['dataframe'] == 'df_final' and r['row_count'] != '']
    raw = [r for r in current if r['event_type'] == 'SOURCE_READ' and r['dataframe'] == 'df_source']
    state = {'RUN_COMPLETED': 'Completed', 'RUN_FAILED': 'Failed'}.get(current[-1]['event_type'], 'In progress')
    all_ids = list(dict.fromkeys((r['run_id'] for r in records)))
    histories = []
    for run in reversed(all_ids):
        group = [r for r in records if r['run_id'] == run]
        histories.append('<details><summary>' + esc(group[0]['timestamp_utc']) + ' · ' + esc(group[-1]['event_type']) + ' · ' + str(len(group)) + ' events · ' + esc(run[:8]) + '</summary>' + table(group) + '</details>')
    latest_ids = list(reversed(all_ids))[:2]
    comparison_panels = []
    for index, run in enumerate(latest_ids):
        group = [r for r in records if r['run_id'] == run]
        heading = 'Latest run' if index == 0 else 'Previous run'
        comparison_panels.append('<article class="compare-panel"><h2>' + heading + '</h2><p class="muted">' + esc(group[0]['timestamp_utc']) + ' · ' + esc(group[-1]['event_type']) + ' · ' + str(len(group)) + ' events</p><p class="detail">Run ' + esc(run) + '</p>' + table(group) + '</article>')
    if len(latest_ids) < 2:
        comparison_panels.append('<article class="compare-panel"><h2>Previous run</h2><p>There is only one retained run. A second run is needed for comparison.</p></article>')
    comparison_html = '<div class="compare-grid">' + ''.join(comparison_panels) + '</div>'
    template = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Data Pipeline Audit Demo</title><style>\n    :root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#19313D;color:#F4EFE6;font:14px/1.5 \'Segoe UI\',Arial,sans-serif}main{max-width:1600px;margin:auto;padding:40px 30px}.crumb{color:#D8A431;margin-bottom:20px}header{display:flex;gap:18px;align-items:center;flex-wrap:wrap}h1{font-size:34px;margin:0;letter-spacing:-1px}.badge{padding:4px 12px;border:1px solid #B8D2C0;background:#264653;color:#B8D2C0;border-radius:6px}.muted,.detail{color:#E8DDCB}.detail{font-size:11px;max-width:440px;overflow-wrap:anywhere;margin-top:5px}nav{display:flex;gap:25px;border-bottom:1px solid #A899C7;padding:20px 0 12px}a{color:#D8A431;text-decoration:none}.cards{display:grid;grid-template-columns:repeat(4,1fr);margin:24px 0;border:1px solid #A899C7;border-radius:10px;background:#264653}.card{padding:18px}.card+.card{border-left:1px solid #A899C7}.label,th{color:#B8D2C0;text-transform:uppercase;font-size:11px;letter-spacing:1px}.value{font-size:25px;font-weight:650;margin-top:5px}h2{font-size:18px;border-left:3px solid #D8A431;padding-left:12px;margin-top:30px}.scroll,.panel{overflow-x:auto}table{width:100%;border-collapse:collapse;text-align:left}th,td{padding:13px 12px;border-bottom:1px solid #19313D;vertical-align:top}td{font-size:12px;color:#E8DDCB}strong{color:#F4EFE6}tbody tr:hover{background:#19313D}.mono{font-family:Consolas,monospace;white-space:nowrap}.panel{padding:20px;border:1px solid #A899C7;background:#264653;border-radius:10px}.note{border-left:3px solid #D8A431;background:#264653;padding:15px;margin-top:22px;color:#E8DDCB}.bad td{color:#F1C6C1}details{margin:12px 0;border:1px solid #A899C7;border-radius:7px;padding:12px}summary{cursor:pointer;color:#D8A431}code{overflow-wrap:anywhere;color:#F1C6C1}footer{border-top:1px solid #A899C7;padding-top:16px;margin-top:30px;color:#B8D2C0;font-size:12px}@media(max-width:800px){main{padding:24px 16px}.cards{grid-template-columns:repeat(2,1fr)}.card+.card{border-left:none}}\n    /* Japanese Color Atlas: https://japanesecoloratlas.com/en ; sRGB digital approximations. */\n.bad td{background:#B33A3A;color:#F4EFE6}\n\n[hidden]{display:none!important}\nnav{padding-bottom:0;overflow-x:auto}\n.tab-button{background:none;border:0;border-bottom:2px solid transparent;color:#E8DDCB;font:inherit;padding:0 0 12px;cursor:pointer;white-space:nowrap}\n.tab-button[aria-selected="true"]{color:#D8A431;border-bottom-color:#D8A431}\n.tab-button:focus-visible{outline:2px solid #A899C7;outline-offset:4px}\nmain{max-width:1900px}\n.compare-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px;align-items:start}\n.compare-panel{min-width:0;background:#264653;border:1px solid #A899C7;border-radius:10px;padding:16px}\n.compare-panel h2{margin-top:0}\n.compare-panel .scroll{max-height:72vh;overflow:auto}\n.compare-panel th{position:sticky;top:0;z-index:1;background:#19313D}\n.compare-panel td,.compare-panel th{padding:10px 8px}\n.compare-panel .detail{min-width:160px}\n@media(max-width:900px){.compare-grid{grid-template-columns:1fr}}\n/* Changed counts: Yamabuki gold, for increases AND decreases. */\n.delta-change{color:#D8A431;font-weight:750}\n.delta-zero{color:#E8DDCB}\n.delta-unavailable{color:#E8DDCB;opacity:.7}\n.source-file-link{color:#D8A431;text-decoration:none;border-bottom:1px dotted #D8A431;display:inline-block;white-space:nowrap}\n.source-file-link:hover{color:#F4EFE6;border-bottom-style:solid}\n.source-file-link:focus-visible{outline:2px solid #A899C7;outline-offset:3px}\n.source-meta{color:#E8DDCB;font-size:11px;margin-top:3px}\nstrong.checkpoint-name[title]{cursor:help}strong.checkpoint-name:focus-visible{outline:2px solid #D8A431;outline-offset:3px}\n\n/* Keep comparison viewport dimensions identical; row heights are paired by JS. */\n.compare-panel .scroll{height:72vh;max-height:72vh;overflow:auto;scrollbar-gutter:stable;overflow-anchor:none}\n.compare-panel table{border-collapse:separate;border-spacing:0}\n\n#compare tbody tr{cursor:pointer}\n#compare tbody tr.step-selected>td{background:#3B5260;box-shadow:inset 0 2px #D8A431,inset 0 -2px #D8A431}\n#compare tbody tr.step-selected>td:first-child{border-left:3px solid #D8A431}\n#compare tbody tr:focus-visible{outline:2px solid #D8A431;outline-offset:-2px}\n</style></head><body><main><div class="crumb">Data Operations / Synthetic Demo</div><header><h1>Data Pipeline Audit Demo</h1><span class="badge">@@STATE@@</span></header><p class="muted">Source reads and meaningful row-count changes — filters, deduplication, mapping joins, and final output.</p><nav role="tablist" aria-label="Audit dashboard">\n<button id="tab-compare" class="tab-button" role="tab" aria-selected="true" aria-controls="compare" data-panel="compare">Compare latest 2 runs</button>\n<button id="tab-stages" class="tab-button" role="tab" aria-selected="false" aria-controls="stages" data-panel="stages" tabindex="-1">Current run</button>\n<button id="tab-flow" class="tab-button" role="tab" aria-selected="false" aria-controls="flow" data-panel="flow" tabindex="-1">Workflow</button>\n<button id="tab-history" class="tab-button" role="tab" aria-selected="false" aria-controls="history" data-panel="history" tabindex="-1">Run history</button></nav><section id="compare" role="tabpanel" aria-labelledby="tab-compare"><h2>Latest two audit runs</h2><p class="muted">Δ = this run minus the same checkpoint in its preceding run. Both positive and negative changes are highlighted in gold; 0 means unchanged. A dash means no comparable count exists. The previous panel compares against its own preceding run.</p>@@COMPARE@@</section><section id="stages" role="tabpanel" aria-labelledby="tab-stages" hidden><div class="cards">\n    <div class="card"><div class="label">Current source rows</div><div class="value">@@RAW@@</div></div><div class="card"><div class="label">Latest df_final rows</div><div class="value">@@FINAL@@</div></div><div class="card"><div class="label">Current run audit events</div><div class="value">@@COUNT@@</div></div><div class="card"><div class="label">Retained runs</div><div class="value">@@RUNS@@</div></div></div>\n    <h2>Current run audit events</h2>@@CURRENT@@</section>\n    <section id="flow" role="tabpanel" aria-labelledby="tab-flow" hidden><h2>Processing workflow</h2><div class="panel"><pre class="mermaid">\nflowchart TD\n    A["Current synthetic source"] --> C["Combine sources"]\n    B["Historical synthetic source"] --> C\n    M["Reference mapping"] --> D["Apply mapping rules"]\n    C --> D\n    D --> E["Keep eligible records"]\n    A --> P["Distinct entities"]\n    T["Target reference"] --> J["Expand entities against targets"]\n    P --> J\n    E --> K["Combine eligible and generated records"]\n    J --> K\n    K --> L["Remove superseded records"]\n    L --> F["Apply final exclusion rule"]\n    Q[("Synthetic audit history")] --> R["Interactive HTML demo"]\n    D -.-> Q\n    K -.-> Q\n    F -.-> Q\n    </pre><p class="muted">Mermaid requires internet access. Counts and history tables work offline.</p></div></section>\n    <section id="history" role="tabpanel" aria-labelledby="tab-history" hidden><h2>Run history · newest first</h2>@@HISTORY@@<div class="note">Δ compares the same checkpoint with the immediately preceding run, including a failed run if applicable. Do not sum rows across stages. Partial runs remain in history. Status changes may leave the row count unchanged.</div><h2>Persistent tracking file</h2><div class="panel"><code>@@PATH@@</code></div></section><footer>Run @@ID@@ · Generated @@TIME@@ · Python timestamps, not Power BI refresh times. Audit stores metadata, not employee records. Run one process at a time and back up the CSV. Opening this HTML does not execute the pipeline.</footer></main><script>\nconst tabs=[...document.querySelectorAll(\'[role="tab"]\')];\nfunction activate(tab){tabs.forEach(item=>{const active=item===tab;item.setAttribute(\'aria-selected\',String(active));item.tabIndex=active?0:-1;document.getElementById(item.dataset.panel).hidden=!active;});if(tab.dataset.panel===\'flow\')window.dispatchEvent(new Event(\'pipeline-flow-visible\'));}\ntabs.forEach((tab,index)=>{tab.addEventListener(\'click\',()=>activate(tab));tab.addEventListener(\'keydown\',event=>{let next;if(event.key===\'ArrowRight\')next=tabs[(index+1)%tabs.length];if(event.key===\'ArrowLeft\')next=tabs[(index+tabs.length-1)%tabs.length];if(event.key===\'Home\')next=tabs[0];if(event.key===\'End\')next=tabs[tabs.length-1];if(next){event.preventDefault();activate(next);next.focus();}});});\n</script>\n<script type="module">\nimport mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";\nmermaid.initialize({startOnLoad:false,theme:"base",securityLevel:"strict",themeVariables:{darkMode:true,background:"#19313D",primaryColor:"#264653",primaryTextColor:"#F4EFE6",primaryBorderColor:"#D8A431",secondaryColor:"#6B4C7A",secondaryTextColor:"#F4EFE6",secondaryBorderColor:"#A899C7",lineColor:"#D8A431",textColor:"#F4EFE6",edgeLabelBackground:"#19313D"}});\nlet rendered=false;\nasync function render(){if(rendered||document.getElementById(\'flow\').hidden)return;rendered=true;try{await mermaid.run({querySelector:\'.mermaid\'});}catch(e){rendered=false;console.warn(e);}}\nwindow.addEventListener(\'pipeline-flow-visible\',render);render();\n</script>\n<script>\n(function(){\n const panels=[...document.querySelectorAll(\'#compare .compare-panel .scroll\')];\n if(panels.length!==2)return;\n const [left,right]=panels;\n let aligning=false;\n function alignRows(){\n   if(aligning||document.getElementById(\'compare\').hidden)return;\n   aligning=true;\n   const a=[...left.querySelectorAll(\'tr\')],b=[...right.querySelectorAll(\'tr\')];\n   [...a,...b].forEach(row=>row.style.height=\'\');\n   // Both runs retain identical checkpoint order. Pair by row position.\n   const heights=[];\n   for(let i=0;i<Math.min(a.length,b.length);i++)heights.push(Math.ceil(Math.max(a[i].getBoundingClientRect().height,b[i].getBoundingClientRect().height)));\n   heights.forEach((height,i)=>{a[i].style.height=height+\'px\';b[i].style.height=height+\'px\';});\n   // Exact pixel offsets now align corresponding checkpoint rows.\n   right.scrollTop=left.scrollTop;\n   aligning=false;\n }\n function sync(from,to){\n   if(Math.abs(to.scrollTop-from.scrollTop)>1)to.scrollTop=from.scrollTop;\n   if(Math.abs(to.scrollLeft-from.scrollLeft)>1)to.scrollLeft=from.scrollLeft;\n }\n left.addEventListener(\'scroll\',()=>sync(left,right),{passive:true});\n right.addEventListener(\'scroll\',()=>sync(right,left),{passive:true});\n let frame;\n function schedule(){cancelAnimationFrame(frame);frame=requestAnimationFrame(alignRows);}\n window.addEventListener(\'resize\',schedule);\n document.querySelector(\'[aria-controls="compare"]\').addEventListener(\'click\',schedule);\n // Handles keyboard activation of tabs as well as mouse clicks.\n new MutationObserver(schedule).observe(document.getElementById(\'compare\'),{attributes:true,attributeFilter:[\'hidden\']});\n if(document.fonts)document.fonts.ready.then(schedule);\n window.addEventListener(\'load\',schedule);\n schedule();\n})();\n</script>\n<script>\n(function(){\n const root=document.getElementById(\'compare\');\n if(!root)return;\n const rows=[...root.querySelectorAll(\'tbody tr[data-step]\')];\n let selected=null;\n function select(row){\n   selected=selected===row.dataset.step?null:row.dataset.step;\n   rows.forEach(item=>{\n     const active=selected!==null&&item.dataset.step===selected;\n     item.classList.toggle(\'step-selected\',active);\n     item.setAttribute(\'aria-selected\',String(active));\n   });\n }\n rows.forEach(row=>{\n   row.tabIndex=0;\n   row.setAttribute(\'aria-selected\',\'false\');\n   row.addEventListener(\'click\',event=>{\n     if(event.target.closest(\'a,button,input,summary\'))return;\n     select(row);\n   });\n   row.addEventListener(\'keydown\',event=>{\n     if(event.target!==row)return;\n     if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();select(row);}\n   });\n });\n root.addEventListener(\'keydown\',event=>{\n   if(event.key===\'Escape\'){\n     selected=null;\n     rows.forEach(row=>{row.classList.remove(\'step-selected\');row.setAttribute(\'aria-selected\',\'false\');});\n   }\n });\n})();\n</script></body></html>'
    values = {'STATE': esc(state), 'RAW': number(raw[-1]['row_count']) if raw else '—', 'FINAL': number(final[-1]['row_count']) if final else '—', 'COUNT': str(len(current)), 'RUNS': str(len(all_ids)), 'CURRENT': table(current, True), 'METRICS': table([r for r in current if r['event_type'] == 'METRIC'], True), 'HISTORY': ''.join(histories), 'PATH': esc(AUDIT_HISTORY.name), 'ID': esc(AUDIT_RUN), 'TIME': esc(_audit_now()), 'COMPARE': comparison_html}
    for name, value in values.items():
        template = template.replace('@@' + name + '@@', value)
    AUDIT_HTML.write_text(template, encoding='utf-8')

def finish_audit():
    """Finalize the current run and rebuild HTML without rerunning processing."""
    global _audit_finished
    if not globals().get('_audit_finished', False):
        _audit_event('RUN_COMPLETED', 'Notebook pipeline completed')
        _audit_finished = True
    _audit_dashboard()
    print('Audit history:', AUDIT_HISTORY)
    print('HTML dashboard:', AUDIT_HTML)
    return AUDIT_HTML
