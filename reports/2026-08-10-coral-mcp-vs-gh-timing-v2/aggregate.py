import json, os, glob

ART = "/Users/viclkykumar/code/coral-mcp-benchmark/reports/2026-08-10-coral-mcp-vs-gh-timing-v2/artifacts"

rows = []
for d in sorted(glob.glob(os.path.join(ART, "t*"))):
    if not os.path.isdir(d):
        continue
    name = os.path.basename(d)
    coral_p = os.path.join(d, "coral", "summary.json")
    gh_p = os.path.join(d, "gh", "summary.json")
    if not (os.path.exists(coral_p) and os.path.exists(gh_p)):
        continue
    coral = json.load(open(coral_p))
    gh = json.load(open(gh_p))
    c_total = coral.get("total", {})
    g_real = gh.get("real", {})
    gh_med = g_real.get("median")
    c_med = c_total.get("median")
    ratio = round(c_med / gh_med, 1) if (c_med and gh_med) else None
    rows.append({
        "test": name,
        "rows": int(coral.get("rows", {}).get("median", 0)) if isinstance(coral.get("rows"), dict) else 0,
        "gh_med": gh_med,
        "coral_med": c_med,
        "coral_init_med": coral.get("init", {}).get("median"),
        "coral_sql_med": coral.get("sql", {}).get("median"),
        "ratio": ratio,
    })

print(json.dumps(rows, indent=2))

with open(os.path.join(ART, "all_summary.json"), "w") as f:
    json.dump(rows, f, indent=2)