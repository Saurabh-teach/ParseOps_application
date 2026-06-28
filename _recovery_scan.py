import json
import os
import urllib.parse
from datetime import datetime
from pathlib import Path

HISTORY = Path(r"C:/Users/saura/AppData/Roaming/Code/User/History")
ROOT = Path(r"C:/Users/saura/ParseOps")
OUT = ROOT / "RECOVERY_REPORT_DATA.json"

hits = []
for folder in HISTORY.iterdir():
    if not folder.is_dir():
        continue
    ep = folder / "entries.json"
    if not ep.exists():
        continue
    try:
        data = json.loads(ep.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        continue
    resource = urllib.parse.unquote(data.get("resource", ""))
    if "ParseOps" not in resource and "ParseOps1" not in resource:
        continue
    for entry in data.get("entries", []):
        fp = folder / entry.get("id", "")
        if not fp.exists():
            continue
        ts = entry.get("timestamp", 0)
        hits.append({
            "resource": resource,
            "history_file": str(fp),
            "size": fp.stat().st_size,
            "timestamp": ts,
            "iso": datetime.fromtimestamp(ts / 1000).isoformat(timespec="seconds") if ts else "",
            "source": entry.get("source", ""),
        })

hits.sort(key=lambda x: x["timestamp"], reverse=True)
OUT.write_text(json.dumps(hits, indent=2), encoding="utf-8")
print(f"Wrote {len(hits)} entries to {OUT}")

large_app = [h for h in hits if "App.jsx" in h["resource"] and h["size"] > 100000]
print(f"Large App.jsx history entries: {len(large_app)}")
for h in large_app[:20]:
    print(h["iso"], h["size"], h["resource"], h["history_file"])
