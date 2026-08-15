"""
Fix v6 (FINAL): for each still-failing table, get the EXACT required filters
from coral.filters (is_required=true), and find parent queries that return
matching column values.

Key insight: coral.filters.filter_name IS the column name. The earlier
catalog used coral.tables.required_filters which was a separate (less accurate)
source.
"""

import json, os, select, subprocess, time, sys

ROOT = "/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-full-test"
TASK_ID = "ccc6ea3e-e759-4e17-a3a9-810d5fa7cde7"

def run_sql(query, timeout=25):
    proc = subprocess.Popen(
        ["coral", "mcp-stdio"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, bufsize=1,
    )
    def send(o): proc.stdin.write(json.dumps(o)+"\n"); proc.stdin.flush()
    def read_response(eid, t):
        deadline = time.time() + t
        while True:
            rem = deadline - time.time()
            if rem <= 0: raise TimeoutError()
            r, _, _ = select.select([proc.stdout], [], [], min(1, rem))
            if not r: continue
            ln = proc.stdout.readline()
            if not ln: continue
            try: o = json.loads(ln)
            except: continue
            if o.get("id") == eid: return o
    try:
        send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"v6","version":"1.0"}}})
        read_response(1, 20)
        send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
        send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql","arguments":{"queries":[query],"intent":"v6","task_id":TASK_ID}}})
        t0 = time.perf_counter()
        try: resp = read_response(2, timeout)
        except TimeoutError: return ("timeout", time.perf_counter()-t0, 0, "timeout")
        elapsed = time.perf_counter() - t0
        res = resp.get("result", {})
        if res.get("isError"):
            err = ""
            for c in res.get("content", []):
                if c.get("type") == "text": err = c.get("text","")[:500]; break
            return ("error", elapsed, 0, err)
        sc = res.get("structuredContent", {})
        results = sc.get("results", [])
        rows = results[0].get("rows", []) if results else []
        return ("data" if len(rows)>0 else "empty", elapsed, len(rows), None)
    except Exception as e:
        return ("crash", 0, 0, str(e)[:400])
    finally:
        try: proc.kill()
        except: pass

def fetch_one(query, value_col):
    """Run query and return first non-null value of value_col."""
    proc = subprocess.Popen(
        ["coral", "mcp-stdio"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, bufsize=1,
    )
    def send(o): proc.stdin.write(json.dumps(o)+"\n"); proc.stdin.flush()
    def read_response(eid, t):
        deadline = time.time() + t
        while True:
            rem = deadline - time.time()
            if rem <= 0: raise TimeoutError()
            r, _, _ = select.select([proc.stdout], [], [], min(1, rem))
            if not r: continue
            ln = proc.stdout.readline()
            if not ln: continue
            try: o = json.loads(ln)
            except: continue
            if o.get("id") == eid: return o
    try:
        send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"v6b","version":"1.0"}}})
        read_response(1, 20)
        send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
        send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql","arguments":{"queries":[query],"intent":"v6b","task_id":TASK_ID}}})
        resp = read_response(2, 20)
        sc = resp.get("result", {}).get("structuredContent", {})
        rows = sc.get("results", [[]])[0].get("rows", []) if sc.get("results") else []
        for row in rows:
            v = row.get(value_col)
            if v not in (None, "", "0"):
                return v
        return None
    except Exception:
        return None
    finally:
        try: proc.kill()
        except: pass

def quote(v):
    return "'" + str(v).replace("'", "''") + "'"

# Step 1: Get the EXACT required filters from coral.filters for all 101 my-fault tables
SMOKE = json.load(open(os.path.join(ROOT, "smoke_results.json")))
FIX3 = json.load(open(os.path.join(ROOT, "fix3_results.json")))
SMART = json.load(open(os.path.join(ROOT, "smart_results.json")))
GHIDS = json.load(open(os.path.join(ROOT, "gh_ids_results.json")))

final = {}
for n, r in SMOKE.items():
    final[n] = {"status": r["status"]}
for name, info in FIX3.get("fixed", []):
    final[name] = {"status": info["status"]}
for name in FIX3.get("rate_limited", []):
    final[name] = {"status": "rate_limited"}
for name in FIX3.get("auth_required", []):
    final[name] = {"status": "auth_required"}
for name in FIX3.get("crash", []):
    final[name] = {"status": "crash"}
for name, info in FIX3.get("bad_request", []):
    final[name] = {"status": "my_fault"}
for name in FIX3.get("no_fix", []):
    final[name] = {"status": "no_real_id"}
for name in SMART.get("fixed", []):
    final[name] = {"status": "data"}
for name in SMART.get("rate_limited", []):
    final[name] = {"status": "rate_limited"}
for name in SMART.get("auth_required", []):
    final[name] = {"status": "auth_required"}
for name in SMART.get("crash", []):
    final[name] = {"status": "crash"}
for name, info in SMART.get("bad_request", []):
    final[name] = {"status": "my_fault"}
for name in SMART.get("no_fix", []):
    final[name] = {"status": "no_real_id"}
for name, status, rows_t, time_t in GHIDS.get("fixed", []):
    final[name] = {"status": status}
for name in GHIDS.get("rate_limited", []):
    final[name] = {"status": "rate_limited"}
for name in GHIDS.get("auth_required", []):
    final[name] = {"status": "auth_required"}
for name in GHIDS.get("crash", []):
    final[name] = {"status": "crash"}
for name, info in GHIDS.get("bad_request", []):
    final[name] = {"status": "my_fault"}
for name in GHIDS.get("no_fix", []):
    final[name] = {"status": "no_real_id"}

to_fix = sorted([n for n, r in final.items() if r["status"] in ("my_fault", "no_real_id")])
print(f"to re-probe with correct filters: {len(to_fix)}", flush=True)

print("Fetching exact required filters from coral.filters...", flush=True)
# Get all required filters for these tables in one query
tables_csv = ",".join(["'" + t.replace("'", "''") + "'" for t in to_fix])
filters_query = f"SELECT table_name, filter_name FROM coral.filters WHERE schema_name='github' AND is_required=true AND table_name IN ({tables_csv}) ORDER BY table_name, filter_name"
status, _, _, _ = run_sql(filters_query, timeout=30)
if status != "data":
    print(f"Failed to fetch filters: {status}")
    sys.exit(1)

# Reload with full rows
proc = subprocess.Popen(["coral", "mcp-stdio"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
def send(o): proc.stdin.write(json.dumps(o)+"\n"); proc.stdin.flush()
def read_response(eid, t):
    deadline = time.time() + t
    while True:
        rem = deadline - time.time()
        if rem <= 0: raise TimeoutError()
        r, _, _ = select.select([proc.stdout], [], [], min(1, rem))
        if not r: continue
        ln = proc.stdout.readline()
        if not ln: continue
        try: o = json.loads(ln)
        except: continue
        if o.get("id") == eid: return o
send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"v6c","version":"1.0"}}})
read_response(1, 20)
send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql","arguments":{"queries":[filters_query],"intent":"v6c","task_id":TASK_ID}}})
resp = read_response(2, 25)
sc = resp.get("result", {}).get("structuredContent", {})
rows = sc.get("results", [[]])[0].get("rows", []) if sc.get("results") else []
proc.kill()

# Build required_filters map
from collections import defaultdict
req_filters = defaultdict(list)
for r in rows:
    req_filters[r["table_name"]].append(r["filter_name"])

# Update CATALOG with correct filters
CATALOG = json.load(open("/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-catalog/tables.json"))
for name, filters in req_filters.items():
    if name in CATALOG:
        CATALOG[name]["required_filters"] = filters
        # also store raw
        CATALOG[name]["required_filters_raw"] = "true" if filters else "false"
json.dump(CATALOG, open(os.path.join(ROOT, "corrected_catalog.json"), "w"), indent=2)
print(f"Updated required_filters for {len(req_filters)} tables", flush=True)

# Resolvers: for each filter name, list of (parent_query, value_col) tries
RESOLVERS = {
    "run_id": [
        ("SELECT id FROM github.repo_action_runs WHERE owner='FiscalMindset' AND repo='coral' ORDER BY created_at DESC LIMIT 3", "id"),
    ],
    "job_id": [
        ("SELECT job_id FROM github.repo_action_jobs WHERE owner='FiscalMindset' AND repo='coral' AND run_id='31300020216' LIMIT 3", "job_id"),
    ],
    "commit_sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 3", "sha"),
    ],
    "sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 3", "sha"),
    ],
    "pull_number": [
        ("SELECT number FROM github.pulls WHERE owner='withcoral' AND repo='coral' AND state='open' LIMIT 3", "number"),
    ],
    "issue_number": [
        ("SELECT number FROM github.issues WHERE owner='withcoral' AND repo='coral' AND state='open' LIMIT 3", "number"),
    ],
    "release_id": [
        ("SELECT id FROM github.releases WHERE owner='withcoral' AND repo='coral' ORDER BY published_at DESC LIMIT 3", "id"),
    ],
    "asset_id": [
        ("SELECT id FROM github.repo_release_assets WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id"),
    ],
    "check_run_id": [
        ("SELECT check_run_id FROM github.repo_check_runs WHERE owner='withcoral' AND repo='coral' LIMIT 3", "check_run_id"),
        ("SELECT id FROM github.repo_check_runs WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id"),
    ],
    "check_suite_id": [
        ("SELECT check_suite_id FROM github.repo_check_suites WHERE owner='withcoral' AND repo='coral' LIMIT 3", "check_suite_id"),
    ],
    "review_id": [
        ("SELECT id FROM github.reviews WHERE owner='withcoral' AND repo='coral' AND pull_number=2116 LIMIT 3", "id"),
    ],
    "thread_id": [
        ("SELECT id FROM github.notifications LIMIT 3", "id"),
    ],
    "comment_id": [
        ("SELECT id FROM github.comments WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id"),
        ("SELECT id FROM github.repo_issue_comments WHERE owner='withcoral' AND repo='coral' AND number=2116 LIMIT 3", "id"),
    ],
    "alert_number": [
        ("SELECT number FROM github.repo_code_scanning_alerts WHERE owner='withcoral' AND repo='coral' LIMIT 3", "number"),
    ],
    "tag": [
        ("SELECT name FROM github.repo_tags WHERE owner='withcoral' AND repo='coral' LIMIT 3", "name"),
    ],
    "tag_sha": [
        ("SELECT commit_sha FROM github.repo_tags WHERE owner='withcoral' AND repo='coral' LIMIT 3", "commit_sha"),
    ],
    "branch": [
        ("SELECT name FROM github.repo_branches WHERE owner='FiscalMindset' AND repo='coral' LIMIT 3", "name"),
    ],
    "ref": [
        ("SELECT ref FROM github.repo_branches WHERE owner='FiscalMindset' AND repo='coral' LIMIT 3", "ref"),
    ],
    "head_sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 3", "sha"),
    ],
    "tree_sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 3", "sha"),
    ],
    "file_sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 3", "sha"),
    ],
    "gist_id": [
        ("SELECT id FROM github.gists WHERE owner='FiscalMindset' LIMIT 3", "id"),
    ],
    "codespace_name": [
        ("SELECT name FROM github.user_codespaces LIMIT 3", "name"),
    ],
    "deployment_id": [
        ("SELECT id FROM github.repo_deployments WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id"),
    ],
    "pages_deployment_id": [
        ("SELECT id FROM github.repo_page_deployments WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id"),
    ],
    "hook_id": [
        ("SELECT id FROM github.repo_hooks WHERE owner='FiscalMindset' AND repo='coral' LIMIT 3", "id"),
    ],
    "runner_id": [
        ("SELECT id FROM github.runners WHERE org='withcoral' LIMIT 3", "id"),
    ],
    "runner_group_id": [
        ("SELECT id FROM github.runner_groups WHERE org='withcoral' LIMIT 3", "id"),
    ],
    "workflow_id": [
        ("SELECT id FROM github.workflows WHERE owner='FiscalMindset' AND repo='coral' LIMIT 3", "id"),
    ],
    "codeql_variant_analysis_id": [
        ("SELECT id FROM github.variant_analyses WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id"),
    ],
    "classroom_id": [
        ("SELECT id FROM github.classrooms LIMIT 3", "id"),
    ],
    "assignment_id": [
        ("SELECT id FROM github.classroom_assignments LIMIT 3", "id"),
    ],
}

STATIC = {
    "attempt_number": "1",
    "environment_name": "production",
    "basehead": "main...main",
    "path": "README.md",
    "package_type": "npm",
    "package_name": "react",
    "actor_type": "User",
    "timestamp_increment": "day",
    "min_timestamp": "2024-01-01T00:00:00Z",
    "day": "2024-01-01",
    "org": "withcoral",
    "enterprise": "FiscalMindset",
    "app_slug": "github",
    "plan_id": "0",
    "devcontainer_path": ".devcontainer/devcontainer.json",
    "network_settings_id": "0",
    "installation_id": "0",
    "actor_id": "0",
    "user_id": "0",
    "team_id": "0",
    "role_id": "0",
    "sarif_id": "0",
    "export_id": "0",
    "image_definition_id": "0",
    "configuration_id": "0",
    "subject_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "ruleset_id": "0",
    "project_number": "0",
    "account_id": "0",
    "enterprise-team": "engineering",
}

def fetch_real_value(filter_name):
    resolvers = RESOLVERS.get(filter_name, [])
    for q, col in resolvers:
        v = fetch_one(q, col)
        if v is not None:
            return v
    return None

def build_query(name, required_filters):
    seen = set(); req = [f for f in required_filters if not (f in seen or seen.add(f))]
    clauses = []
    resolved = {}
    for f in req:
        if f in ("owner", "repo", "username", "user"):
            continue
        v = fetch_real_value(f)
        if v is not None:
            clauses.append(f"{f}={quote(v)}")
            resolved[f] = v
            continue
        if f in STATIC:
            clauses.append(f"{f}={quote(STATIC[f])}")
            continue
        return None, resolved
    if "owner" in req: clauses.append("owner='withcoral'")
    if "repo" in req: clauses.append("repo='coral'")
    if "username" in req or "user" in req: clauses.append("username='FiscalMindset'")
    if not clauses:
        return f"SELECT * FROM github.{name} LIMIT 1", resolved
    return f"SELECT * FROM github.{name} WHERE " + " AND ".join(clauses) + " LIMIT 1", resolved

def classify_error(msg):
    m = msg.lower()
    if 'rate limit' in m or '429' in m: return "rate_limited"
    if '404' in m or 'not found' in m: return "not_found"
    if '401' in m or '403' in m or 'forbidden' in m: return "auth_required"
    if '400' in m or '422' in m or 'validation' in m: return "bad_request"
    if 'no column' in m or 'no table' in m: return "no_column"
    return "other_error"

results = {"fixed": [], "rate_limited": [], "auth_required": [], "bad_request": [], "no_fix": [], "no_column": []}
i = 0
for name in to_fix:
    i += 1
    if name not in req_filters:
        # No required filters known, fall back to no filters
        req = []
    else:
        req = req_filters[name]
    q, resolved = build_query(name, req)
    if q is None:
        results["no_fix"].append(name)
        sys.stderr.write(f"[{i}/{len(to_fix)}] {name:50s} NO_FIX req={req}\n")
        sys.stderr.flush()
        continue
    status, elapsed, rows, err = run_sql(q, timeout=25)
    if status in ("data", "empty"):
        results["fixed"].append((name, status, rows, elapsed, resolved))
        emoji = "✅" if status == "data" else "∅"
        sys.stderr.write(f"[{i}/{len(to_fix)}] {name:50s} {emoji} {status} rows={rows} t={elapsed:.1f}s\n")
    elif status == "crash":
        results["crash"].append(name)
        sys.stderr.write(f"[{i}/{len(to_fix)}] {name:50s} 💥 CRASH\n")
    else:
        cat = classify_error(err or "")
        if cat == "rate_limited":
            results["rate_limited"].append(name)
            sys.stderr.write(f"[{i}/{len(to_fix)}] {name:50s} ⏱ RATE_LIMITED\n")
        elif cat == "auth_required":
            results["auth_required"].append(name)
            sys.stderr.write(f"[{i}/{len(to_fix)}] {name:50s} 🔒 AUTH\n")
        elif cat == "no_column":
            results["no_column"].append((name, err))
            sys.stderr.write(f"[{i}/{len(to_fix)}] {name:50s} ❌ NO_COLUMN err={(err or '')[:120]}\n")
        else:
            results["bad_request"].append((name, err))
            sys.stderr.write(f"[{i}/{len(to_fix)}] {name:50s} ❌ {cat} err={(err or '')[:80]}\n")
    sys.stderr.flush()
    if i % 5 == 0:
        json.dump(results, open(os.path.join(ROOT, "v6_results.json"), "w"), default=str, indent=2)
        sys.stderr.write("  [saved checkpoint]\n")

json.dump(results, open(os.path.join(ROOT, "v6_results.json"), "w"), default=str, indent=2)
print(f"\nDONE.")
for k, v in results.items():
    print(f"  {k}: {len(v)}")