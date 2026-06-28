import json
import urllib.parse
from datetime import datetime
from pathlib import Path

root = Path(r"C:/Users/saura/ParseOps/frontend")
history = Path(r"C:/Users/saura/AppData/Roaming/Code/User/History")

components = list((root / "src" / "components").rglob("*.jsx"))
components += [
    root / "src" / "api.js",
    root / "eslint.config.js",
    root / "vite.config.js",
    root / "public" / "sw.js",
]

hist_map = {}
for folder in history.iterdir():
    ep = folder / "entries.json"
    if not ep.exists():
        continue
    try:
        data = json.loads(ep.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        continue
    res = urllib.parse.unquote(data.get("resource", ""))
    if "ParseOps/frontend" not in res.replace("\\", "/"):
        continue
    name = res.split("/")[-1]
    entries = sorted(data.get("entries", []), key=lambda e: e.get("timestamp", 0), reverse=True)
    if not entries:
        continue
    fp = folder / entries[0]["id"]
    if fp.exists():
        hist_map[name] = {
            "history_file": str(fp),
            "history_size": fp.stat().st_size,
            "timestamp": entries[0].get("timestamp", 0),
            "source": entries[0].get("source", ""),
            "resource": res,
        }

report = []
for p in sorted(components):
    rel = str(p.relative_to(root)).replace("\\", "/")
    item = {
        "path": rel,
        "current_bytes": p.stat().st_size,
        "current_mtime": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
    }
    h = hist_map.get(p.name)
    if h:
        item["vscode_history"] = h
        item["size_delta"] = item["current_bytes"] - h["history_size"]
    report.append(item)

out = root.parent / "RECOVERY_COMPONENT_SCAN.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"Wrote {out}")
for item in report:
    h = item.get("vscode_history")
    if h:
        print(
            f"{item['path']} | cur={item['current_bytes']} hist={h['history_size']} "
            f"delta={item['size_delta']} | {h.get('source', '')[:80]}"
        )
    else:
        print(f"{item['path']} | cur={item['current_bytes']} | NO_VSCODE_HISTORY")
