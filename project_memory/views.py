"""Small human-readable projections; never authoritative project state."""
from html import escape
import csv
import io
import os
import uuid

from .store import now


def health(store):
    events = store.timeline(1000)
    live = [e for e in events if e.get("origin") == "codex_hook"]
    return {
        "configured": (store.root / ".codex" / "hooks.json").exists(),
        "last_observed_hook": live[0] if live else None,
        "coverage": "Supported local tool events only. Hosted web tools and model reasoning are not recorded. Raw prompts, commands and outputs are not copied; transcript references identify original detail.",
        "activation": "Configured is not active. Codex requires project/hook trust. A non-synthetic event is evidence of delivery at that time, not a permanent guarantee.",
        "semantic_updates": "The agent must record meaningful decisions, feedback and task changes using put/event. Hooks cannot infer their meaning."
    }


def dashboard(store):
    project = store.get("project")
    current = store.get(project["focus"])
    tracker = io.StringIO(newline="")
    writer = csv.writer(tracker)
    writer.writerow(["Goal", project["summary"], "", ""])
    writer.writerow(["Where we are", current["summary"], "", ""])
    writer.writerow(["Next", current.get("next_action", "Discuss with Lohith."), "", ""])
    writer.writerow([])
    writer.writerow(["Checkpoint", "What this achieves", "Status", "Next action"])
    for key in project.get("checkpoints", []):
        item = store.get(key)
        writer.writerow([item["title"], item["summary"], item.get("status", ""), item.get("next_action", "")])
    for destination in (store.root / "PROGRESS-TRACKER.csv", store.home / "cache" / "checkpoints.csv"):
        content = tracker.getvalue().encode("utf-8-sig")
        if not destination.exists() or destination.read_bytes() != content:
            temporary = destination.with_name(uuid.uuid4().hex + ".csv.tmp")
            temporary.write_bytes(content)
            os.replace(temporary, destination)
    h = health(store)
    e = lambda value: escape(str(value))
    rows = []
    for ident in project.get("checkpoints", []):
        r = store.get(ident)
        rows.append(f"<tr><td>{e(ident)}</td><td><strong>{e(r['title'])}</strong><br>{e(r['summary'])}</td><td>{e(r.get('status') or 'Not started')}</td></tr>")
    timeline = []
    for r in store.timeline(16):
        timing = f" · {r['elapsed_ms']} ms" if r.get("elapsed_ms") is not None else ""
        timeline.append(f"<li><time>{e(r.get('time','unknown'))}</time> <b>{e(r['kind'])}</b>{e(timing)}<br>{e(r['summary'])}<small>{e(r.get('record') or '')} {e(r.get('origin') or 'recorded locally')}</small></li>")
    linked = []
    for link in current.get("links", []):
        r = store.get(link["to"])
        linked.append(f"<li>{e(link['rel'])} → <code>{e(r['id'])}</code>: {e(r['title'])}</li>")
    observation = "No live Codex hook event observed yet. Review /hooks in Codex CLI; the next chat must check health."
    if h["last_observed_hook"]:
        last = h["last_observed_hook"]
        observation = "Last delivered hook: " + last["kind"] + " at " + last["time"]
    html = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="refresh" content="5">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Application project — where we are</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;background:#f3f5f7;color:#162536;max-width:1050px;margin:32px auto;padding:0 20px}}h1{{font-size:30px}}h2{{font-size:20px;margin-top:0}}section{{background:white;padding:24px;margin:18px 0;border:1px solid #d7e0e7;border-radius:12px}}.current{{border-left:6px solid #247d75}}small,time{{color:#5e6c78;font-size:13px}}small{{display:block}}table{{border-collapse:collapse;width:100%}}td,th{{text-align:left;padding:14px 9px;border-bottom:1px solid #ddd;vertical-align:top}}td:first-child{{white-space:nowrap}}li{{margin:12px 0}}code{{background:#edf2f6;padding:2px 4px}}.note{{background:#fff5db}}pre{{white-space:pre-wrap}}</style>
<h1>Job-application project</h1><p><strong>Finish line:</strong> {e(project['summary'])}</p>
<section class="current"><h2>We are here: {e(current['title'])}</h2><p>{e(current['summary'])}</p><p><strong>Next:</strong> {e(current.get('next_action','Discuss with Lohith.'))}</p><small>Record {e(current['id'])}, revision {current['revision']}. Page generated {e(now())}.</small></section>
<section><h2>The route to a working application</h2><table><thead><tr><th>Step</th><th>Outcome</th><th>State</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
<section class="note"><h2>What is being recorded</h2><p>{e(observation)}</p><p>Memory changes are recorded by this harness. Tool events arrive only when Codex hooks are trusted and running. Decisions and feedback still need the agent to save their meaning. This page refreshes every five seconds; it is regenerated when hooks or memory commands run.</p></section>
<section><h2>Latest recorded activity</h2><ol>{''.join(timeline)}</ol></section>
<section><h2>Detail connected to the current step</h2><ul>{''.join(linked)}</ul><p>Agent command: <code>scripts/project-memory.ps1 show RECORD-ID</code>. Full exact passages: <code>source SOURCE-SECTION-ID</code>.</p></section>
<section><h2>Your controls</h2><p>Speak normally: ask for an explanation, report a flaw, change a requirement, stop, or resume. The agent must show what a significant change affects before implementing it. A technical result awaits your acceptance; it does not automatically finish a checkpoint.</p></section></html>"""
    path = store.home / "cache" / "status.html"
    temporary = path.with_name(uuid.uuid4().hex + ".html.tmp")
    temporary.write_text(html, encoding="utf-8")
    os.replace(temporary, path)
    return str(path)
