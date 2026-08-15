"""
Fix v8 (FINAL): try multiple alternative values per filter.
For each still-failing table, try the required filter with:
- Static fallback values (correct format)
- Multiple known-good IDs from gh
- Multiple formats (e.g., ref='heads/main' vs 'refs/heads/main')
"""

import json, os, select, subprocess, time, sys

ROOT = "/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-full-test"
TASK_ID = "ccc6ea3e-e759-4e17-a3a9-810d5fa7cde7"

def run_sql(query, timeout=25):
    proc = subprocess.Popen(["coral", "mcp-stdio"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    def send(o): proc.stdin.write(json.dumps(o)+"\n"); proc.stdin.flush()
    def read(eid, t):
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
        send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"v8","version":"1.0"}}})
        read(1, 20)
        send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
        send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql","arguments":{"queries":[query],"intent":"v8","task_id":TASK_ID}}})
        t0 = time.perf_counter()
        try: resp = read(2, timeout)
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
    proc = subprocess.Popen(["coral", "mcp-stdio"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    def send(o): proc.stdin.write(json.dumps(o)+"\n"); proc.stdin.flush()
    def read(eid, t):
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
        send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"v8b","version":"1.0"}}})
        read(1, 20)
        send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
        send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql","arguments":{"queries":[query],"intent":"v8b","task_id":TASK_ID}}})
        resp = read(2, 20)
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

# Alternative values - try multiple options for each filter
# Each entry: list of (parent_query, value_col, format_fn or None)
ALTERNATIVES = {
    "run_id": [
        ("SELECT id FROM github.repo_action_runs WHERE owner='FiscalMindset' AND repo='coral' ORDER BY created_at DESC LIMIT 3", "id", None),
        ("SELECT id FROM github.repo_action_runs WHERE owner='withcoral' AND repo='coral' ORDER BY created_at DESC LIMIT 3", "id", None),
    ],
    "job_id": [
        ("SELECT job_id FROM github.repo_action_jobs WHERE owner='FiscalMindset' AND repo='coral' AND run_id='31300020216' LIMIT 3", "job_id", None),
    ],
    "commit_sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 3", "sha", None),
    ],
    "sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 3", "sha", None),
    ],
    "pull_number": [
        ("SELECT number FROM github.pulls WHERE owner='withcoral' AND repo='coral' AND state='open' LIMIT 3", "number", None),
    ],
    "issue_number": [
        ("SELECT number FROM github.issues WHERE owner='withcoral' AND repo='coral' AND state='open' LIMIT 3", "number", None),
    ],
    "release_id": [
        ("SELECT id FROM github.releases WHERE owner='withcoral' AND repo='coral' ORDER BY published_at DESC LIMIT 3", "id", None),
    ],
    "asset_id": [
        ("SELECT id FROM github.repo_release_assets WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id", None),
    ],
    "check_run_id": [
        ("SELECT id FROM github.repo_check_runs WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id", None),
    ],
    "check_suite_id": [
        ("SELECT check_suite_id FROM github.repo_check_suites WHERE owner='withcoral' AND repo='coral' LIMIT 3", "check_suite_id", None),
    ],
    "review_id": [
        ("SELECT id FROM github.reviews WHERE owner='withcoral' AND repo='coral' AND pull_number=2116 LIMIT 3", "id", None),
    ],
    "thread_id": [
        ("SELECT id FROM github.notifications LIMIT 3", "id", None),
    ],
    "comment_id": [
        ("SELECT id FROM github.comments WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id", None),
    ],
    "alert_number": [
        ("SELECT number FROM github.repo_code_scanning_alerts WHERE owner='withcoral' AND repo='coral' LIMIT 3", "number", None),
    ],
    "tag": [
        ("SELECT name FROM github.repo_tags WHERE owner='withcoral' AND repo='coral' LIMIT 3", "name", None),
    ],
    "tag_sha": [
        ("SELECT commit_sha FROM github.repo_tags WHERE owner='withcoral' AND repo='coral' LIMIT 3", "commit_sha", None),
    ],
    "branch": [
        ("SELECT name FROM github.repo_branches WHERE owner='FiscalMindset' AND repo='coral' LIMIT 3", "name", None),
    ],
    "head_sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 3", "sha", None),
    ],
    "tree_sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 3", "sha", None),
    ],
    "file_sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 3", "sha", None),
    ],
    "gist_id": [
        ("SELECT id FROM github.gists WHERE owner='FiscalMindset' LIMIT 3", "id", None),
    ],
    "codespace_name": [
        ("SELECT name FROM github.user_codespaces LIMIT 3", "name", None),
    ],
    "deployment_id": [
        ("SELECT id FROM github.repo_deployments WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id", None),
    ],
    "pages_deployment_id": [
        ("SELECT id FROM github.repo_page_deployments WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id", None),
    ],
    "hook_id": [
        ("SELECT id FROM github.repo_hooks WHERE owner='FiscalMindset' AND repo='coral' LIMIT 3", "id", None),
    ],
    "runner_id": [
        ("SELECT id FROM github.runners WHERE org='withcoral' LIMIT 3", "id", None),
    ],
    "runner_group_id": [
        ("SELECT id FROM github.runner_groups WHERE org='withcoral' LIMIT 3", "id", None),
    ],
    "workflow_id": [
        ("SELECT id FROM github.workflows WHERE owner='FiscalMindset' AND repo='coral' LIMIT 3", "id", None),
    ],
    "codeql_variant_analysis_id": [
        ("SELECT id FROM github.variant_analyses WHERE owner='withcoral' AND repo='coral' LIMIT 3", "id", None),
    ],
    "classroom_id": [
        ("SELECT id FROM github.classrooms LIMIT 3", "id", None),
    ],
    "assignment_id": [
        ("SELECT id FROM github.classroom_assignments LIMIT 3", "id", None),
    ],
}

# Hand-crafted fixes for specific tables where the value format matters
SPECIFIC_FIXES = {
    "apps": {"app_slug": "github-actions"},
    "attempts": {"attempt_number": "1"},
    "ref": {"ref": "heads/main"},  # needs prefix
}

# Static defaults for things that don't have a real resolver
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
    "app_slug": "github-actions",
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

def get_alternatives(filter_name, table_name):
    """Yield alternative values for a filter, in order of preference."""
    # Check specific fixes first
    if table_name in SPECIFIC_FIXES and filter_name in SPECIFIC_FIXES[table_name]:
        yield SPECIFIC_FIXES[table_name][filter_name]
    # Try resolvers
    for q, col, fmt in ALTERNATIVES.get(filter_name, []):
        v = fetch_one(q, col)
        if v is not None:
            yield v
    # Static fallback
    if filter_name in STATIC:
        yield STATIC[filter_name]

def build_query(name, required_filters):
    seen = set(); req = [f for f in required_filters if not (f in seen or seen.add(f))]
    clauses = []
    resolved = {}
    for f in req:
        if f in ("owner", "repo", "username", "user"):
            continue
        used = None
        for v in get_alternatives(f, name):
            used = v
            break
        if used is not None:
            clauses.append(f"{f}={quote(used)}")
            resolved[f] = used
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

# Load previous state
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
print(f"to re-probe: {len(to_fix)}", flush=True)

# Get filters
tables_csv = ",".join(["'" + t.replace("'", "''") + "'" for t in to_fix])
filters_query = f"SELECT DISTINCT table_name, filter_name FROM coral.filters WHERE schema_name='github' AND is_required=true AND table_name IN ({tables_csv}) ORDER BY table_name, filter_name"
status, _, _, _ = run_sql(filters_query, timeout=30)
if status != "data":
    print(f"Failed: {status}")
    sys.exit(1)

proc = subprocess.Popen(["coral", "mcp-stdio"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
def send2(o): proc.stdin.write(json.dumps(o)+"\n"); proc.stdin.flush()
def read2(eid, t):
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
send2({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"v8c","version":"1.0"}}})
read2(1, 20)
send2({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
send2({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql","arguments":{"queries":[filters_query],"intent":"v8c","task_id":TASK_ID}}})
resp = read2(2, 25)
sc = resp.get("result", {}).get("structuredContent", {})
rows = sc.get("results", [[]])[0].get("rows", []) if sc.get("results") else []
proc.kill()

from collections import defaultdict
req_filters = defaultdict(list)
for r in rows:
    req_filters[r["table_name"]].append(r["filter_name"])

print(f"filters for {len(req_filters)} tables", flush=True)

results = {"fixed": [], "rate_limited": [], "auth_required": [], "bad_request": [], "no_fix": [], "no_column": []}
i = 0
for name in to_fix:
    i += 1
    req = req_filters.get(name, [])
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
        json.dump(results, open(os.path.join(ROOT, "v8_results.json"), "w"), default=str, indent=2)
        sys.stderr.write("  [saved checkpoint]\n")

json.dump(results, open(os.path.join(ROOT, "v8_results.json"), "w"), default=str, indent=2)
print(f"\nDONE.")
for k, v in results.items():
    print(f"  {k}: {len(v)}")