"""
Fix pass v4: use gh CLI to fetch real IDs, then re-probe all 114 my-fault errors.

This time we use gh directly (faster, more reliable) to get real entity IDs
instead of running coral queries to discover them.
"""

import json, os, select, subprocess, time, sys

ROOT = "/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-full-test"
SMOKE = json.load(open(os.path.join(ROOT, "smoke_results.json")))
FIX3 = json.load(open(os.path.join(ROOT, "fix3_results.json")))
SMART = json.load(open(os.path.join(ROOT, "smart_results.json")))
CATALOG = json.load(open("/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-catalog/tables.json"))
TASK_ID = "f0ef7474-10da-4ff0-9973-60342b3bb0d9"

# Load IDs discovered via gh CLI
GH_IDS = json.load(open('/tmp/gh_ids.json'))

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
        send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"v4","version":"1.0"}}})
        read_response(1, 20)
        send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
        send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql","arguments":{"queries":[query],"intent":"v4","task_id":TASK_ID}}})
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

def quote(v):
    return "'" + str(v).replace("'", "''") + "'"

# Static defaults for things we can't easily get
STATIC = {
    "attempt_number": "1",
    "environment_name": "production",
    "basehead": "main...main",
    "path": "README.md",
    "package_type": "npm",
    "package_name": "left-pad",
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
    "run_id": GH_IDS.get("run_id", "31300020216"),
    "job_id": GH_IDS.get("job_id"),
    "gist_id": GH_IDS.get("gist_id"),
    "commit_sha": GH_IDS.get("commit_sha"),
    "issue_number": GH_IDS.get("issue_number"),
    "pull_number": GH_IDS.get("pull_number"),
    "branch": GH_IDS.get("branch", "main"),
    "tag": GH_IDS.get("tag", "v0.9.0"),
    "release_id": GH_IDS.get("release_id"),
    "asset_id": GH_IDS.get("asset_id"),
    "thread_id": GH_IDS.get("thread_id"),
    "comment_id": GH_IDS.get("comment_id"),
    "review_id": GH_IDS.get("review_id"),
    "tag_sha": GH_IDS.get("tag_sha"),
    "tree_sha": GH_IDS.get("tree_sha"),
    "alert_number": GH_IDS.get("alert_number"),
    "head_sha": GH_IDS.get("commit_sha"),
    "ref": GH_IDS.get("branch", "main"),
    "check_run_id": GH_IDS.get("check_run_id"),
    "check_suite_id": GH_IDS.get("check_suite_id"),
    "hook_id": GH_IDS.get("hook_id"),
    "deployment_id": GH_IDS.get("deployment_id"),
    "pages_deployment_id": GH_IDS.get("pages_deployment_id"),
    "runner_id": GH_IDS.get("runner_id"),
    "runner_group_id": "0",
    "codeql_variant_analysis_id": GH_IDS.get("codeql_variant_id"),
    "classroom_id": GH_IDS.get("classroom_id"),
    "assignment_id": "0",
    "export_id": "0",
    "sarif_id": "0",
    "file_sha": GH_IDS.get("commit_sha"),
    "subject_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "ruleset_id": "0",
    "project_number": "0",
    "image_definition_id": "0",
    "configuration_id": "0",
    "account_id": "0",
    "enterprise-team": "engineering",
    "codespace_name": GH_IDS.get("codespace_name"),
}

# remove None values
for k, v in list(STATIC.items()):
    if v is None:
        STATIC[k] = "0"

def classify_error(msg):
    m = msg.lower()
    if 'rate limit' in m or '429' in m: return "rate_limited"
    if '404' in m or 'not found' in m: return "not_found"
    if '401' in m or '403' in m or 'forbidden' in m: return "auth_required"
    if '400' in m or '422' in m or 'validation' in m: return "bad_request"
    return "other_error"

def build_query(name):
    req = CATALOG[name]["required_filters"]
    seen = set(); req = [f for f in req if not (f in seen or seen.add(f))]
    clauses = []
    for f in req:
        if f in ("owner", "repo", "username", "user"):
            continue
        if f in STATIC:
            clauses.append(f"{f}={quote(STATIC[f])}")
            continue
        return None
    if "owner" in req: clauses.append("owner='withcoral'")
    if "repo" in req: clauses.append("repo='coral'")
    if "username" in req or "user" in req: clauses.append("username='FiscalMindset'")
    if not clauses:
        return f"SELECT * FROM github.{name} LIMIT 1"
    return f"SELECT * FROM github.{name} WHERE " + " AND ".join(clauses) + " LIMIT 1"

# Compute the still-failing list from combined fix3 + smart
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
    final[name] = {"status": "my_fault_404"}
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
    final[name] = {"status": "my_fault_404"}
for name in SMART.get("no_fix", []):
    final[name] = {"status": "no_real_id"}

to_fix = sorted([n for n, r in final.items() if r["status"] in ("my_fault_404", "no_real_id")])
print(f"to re-probe with gh-fetched IDs: {len(to_fix)}", flush=True)

results = {"fixed": [], "rate_limited": [], "auth_required": [], "bad_request": [], "no_fix": [], "crash": []}
i = 0
for name in to_fix:
    i += 1
    q = build_query(name)
    if q is None:
        results["no_fix"].append(name)
        sys.stderr.write(f"[{i}/{len(to_fix)}] {name:50s} NO_FIX\n")
        sys.stderr.flush()
        continue
    status, elapsed, rows, err = run_sql(q, timeout=25)
    if status in ("data", "empty"):
        results["fixed"].append((name, status, rows, elapsed))
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
        else:
            results["bad_request"].append((name, err))
            sys.stderr.write(f"[{i}/{len(to_fix)}] {name:50s} ❌ {cat} err={(err or '')[:80]}\n")
    sys.stderr.flush()
    if i % 10 == 0:
        json.dump(results, open(os.path.join(ROOT, "gh_ids_results.json"), "w"), default=str, indent=2)

json.dump(results, open(os.path.join(ROOT, "gh_ids_results.json"), "w"), default=str, indent=2)
print(f"\nDONE.")
for k, v in results.items():
    print(f"  {k}: {len(v)}")