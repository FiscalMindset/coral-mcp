"""
Smarter fix pass: discover real IDs more aggressively, re-probe remaining failures.

For each remaining failure (bad_request + no_fix), try multiple parent queries
per filter to find real values.
"""

import json, os, select, subprocess, time, sys

ROOT = "/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-full-test"
CATALOG = json.load(open("/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-catalog/tables.json"))
TASK_ID = "f0ef7474-10da-4ff0-9973-60342b3bb0d9"

def run_sql_capture(query, timeout=25):
    """Run SQL and return (status, rows, time, error)."""
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
        send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"sm","version":"1.0"}}})
        read_response(1, 20)
        send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
        send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql","arguments":{"queries":[query],"intent":"sm","task_id":TASK_ID}}})
        t0 = time.perf_counter()
        try: resp = read_response(2, timeout)
        except TimeoutError: return ("timeout", [], time.perf_counter()-t0, "timeout")
        elapsed = time.perf_counter() - t0
        res = resp.get("result", {})
        if res.get("isError"):
            err = ""
            for c in res.get("content", []):
                if c.get("type") == "text": err = c.get("text","")[:500]; break
            return ("error", [], elapsed, err)
        sc = res.get("structuredContent", {})
        results = sc.get("results", [])
        rows = results[0].get("rows", []) if results else []
        return ("data" if len(rows)>0 else "empty", rows, elapsed, None)
    except Exception as e:
        try: proc.kill()
        except: pass
        return ("crash", [], 0, str(e)[:400])
    finally:
        try: proc.kill()
        except: pass

def quote(v):
    return "'" + str(v).replace("'", "''") + "'"

# ===== Multiple parent queries per filter =====

# For each filter that needs a real ID, list candidate parent queries (in priority order)
RESOLVERS = {
    "check_run_id": [
        ("SELECT check_run_id FROM github.repo_check_runs WHERE owner='withcoral' AND repo='coral' LIMIT 1", "check_run_id"),
        ("SELECT id FROM github.repo_check_runs WHERE owner='withcoral' AND repo='coral' LIMIT 1", "id"),
    ],
    "check_suite_id": [
        ("SELECT check_suite_id FROM github.repo_check_suites WHERE owner='withcoral' AND repo='coral' LIMIT 1", "check_suite_id"),
        ("SELECT id FROM github.repo_check_suites WHERE owner='withcoral' AND repo='coral' LIMIT 1", "id"),
    ],
    "gist_id": [
        ("SELECT id FROM github.gists WHERE owner='FiscalMindset' LIMIT 1", "id"),
        ("SELECT gist_id FROM github.gists WHERE owner='FiscalMindset' LIMIT 1", "gist_id"),
        ("SELECT id FROM github.gist_public LIMIT 1", "id"),
    ],
    "sha": [
        ("SELECT sha FROM github.gist_commits LIMIT 1", "sha"),
    ],
    "tag_sha": [
        ("SELECT commit_sha FROM github.repo_tags WHERE owner='withcoral' AND repo='coral' LIMIT 1", "commit_sha"),
        ("SELECT sha FROM github.repo_git_tags WHERE owner='withcoral' AND repo='coral' LIMIT 1", "sha"),
    ],
    "job_id": [
        ("SELECT job_id FROM github.repo_action_jobs WHERE owner='FiscalMindset' AND repo='coral' AND run_id='31300020216' LIMIT 1", "job_id"),
    ],
    "workflow_id": [
        ("SELECT id FROM github.workflows WHERE owner='FiscalMindset' AND repo='coral' LIMIT 1", "id"),
        ("SELECT workflow_id FROM github.workflows WHERE owner='FiscalMindset' AND repo='coral' LIMIT 1", "workflow_id"),
    ],
    "thread_id": [
        ("SELECT id FROM github.notifications LIMIT 1", "id"),
        ("SELECT thread_id FROM github.notifications LIMIT 1", "thread_id"),
    ],
    "review_id": [
        ("SELECT id FROM github.reviews WHERE owner='withcoral' AND repo='coral' AND pull_number=1 LIMIT 1", "id"),
    ],
    "alert_number": [
        ("SELECT number FROM github.repo_code_scanning_alerts WHERE owner='withcoral' AND repo='coral' LIMIT 1", "number"),
        ("SELECT number FROM github.repo_secret_scanning_alerts WHERE owner='withcoral' AND repo='coral' LIMIT 1", "number"),
        ("SELECT number FROM github.repo_dependabot_alerts WHERE owner='withcoral' AND repo='coral' LIMIT 1", "number"),
    ],
    "codeql_variant_analysis_id": [
        ("SELECT id FROM github.variant_analyses WHERE owner='withcoral' AND repo='coral' LIMIT 1", "id"),
        ("SELECT codeql_variant_analysis_id FROM github.variant_analyses WHERE owner='withcoral' AND repo='coral' LIMIT 1", "codeql_variant_analysis_id"),
    ],
    "asset_id": [
        ("SELECT id FROM github.repo_release_assets WHERE owner='withcoral' AND repo='coral' LIMIT 1", "id"),
    ],
    "commit_sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 1", "sha"),
        ("SELECT sha FROM github.commits WHERE owner='withcoral' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 1", "sha"),
    ],
    "tree_sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 1", "sha"),
    ],
    "head_sha": [
        ("SELECT sha FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 1", "sha"),
    ],
    "comment_id": [
        ("SELECT id FROM github.repo_issue_comments WHERE owner='withcoral' AND repo='coral' LIMIT 1", "id"),
        ("SELECT id FROM github.issues_list_comments WHERE owner='withcoral' AND repo='coral' LIMIT 1", "id"),
        ("SELECT id FROM github.repo_pull_comments WHERE owner='withcoral' AND repo='coral' LIMIT 1", "id"),
    ],
    "pull_number": [
        ("SELECT number FROM github.pulls WHERE owner='withcoral' AND repo='coral' AND state='open' LIMIT 1", "number"),
        ("SELECT number FROM github.issues WHERE owner='withcoral' AND repo='coral' AND state='open' LIMIT 1", "number"),
    ],
    "issue_number": [
        ("SELECT number FROM github.issues WHERE owner='withcoral' AND repo='coral' AND state='open' LIMIT 1", "number"),
    ],
    "branch": [
        ("SELECT name FROM github.repo_branches WHERE owner='FiscalMindset' AND repo='coral' LIMIT 1", "name"),
    ],
    "tag": [
        ("SELECT name FROM github.repo_tags WHERE owner='withcoral' AND repo='coral' LIMIT 1", "name"),
    ],
    "ref": [
        ("SELECT name FROM github.repo_branches WHERE owner='FiscalMindset' AND repo='coral' LIMIT 1", "name"),
    ],
    "ruleset_id": [
        ("SELECT id FROM github.rulesets WHERE org='withcoral' LIMIT 1", "id"),
    ],
    "project_number": [
        ("SELECT number FROM github.projects_v2 WHERE org='withcoral' LIMIT 1", "number"),
    ],
    "codespace_name": [
        ("SELECT name FROM github.user_codespaces LIMIT 1", "name"),
        ("SELECT codespace_name FROM github.user_codespaces LIMIT 1", "codespace_name"),
    ],
}

STATIC = {
    "attempt_number": "1",
    "environment_name": "production",
    "basehead": "main...main",
    "path": "README.md",
    "package_type": "container",
    "actor_type": "User",
    "timestamp_increment": "day",
    "min_timestamp": "2024-01-01T00:00:00Z",
    "day": "2024-01-01",
    "package_name": "left-pad",
    "org": "withcoral",
    "enterprise": "withcoral",
    "app_slug": "github",
    "plan_id": "0",
    "devcontainer_path": ".devcontainer/devcontainer.json",
    "network_settings_id": "0",
    "installation_id": "0",
    "actor_id": "0",
    "user_id": "0",
    "team_id": "0",
    "role_id": "0",
    "assignment_id": "0",
    "classroom_id": "0",
    "image_definition_id": "0",
    "configuration_id": "0",
    "export_id": "0",
    "deployment_id": "0",
    "pages_deployment_id": "0",
    "sarif_id": "0",
    "file_sha": "0",
    "account_id": "0",
    "hook_id": "0",
    "runner_id": "0",
    "runner_group_id": "0",
    "enterprise-team": "engineering",
    "subject_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
}

def fetch_with_resolvers(filter_name):
    resolvers = RESOLVERS.get(filter_name, [])
    for q, col in resolvers:
        status, rows, _, _ = run_sql_capture(q, timeout=20)
        if status == "data" and rows:
            for row in rows:
                v = row.get(col)
                if v not in (None, "", "0"):
                    return v
    return None

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
        v = fetch_with_resolvers(f)
        if v is not None:
            clauses.append(f"{f}={quote(v)}")
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

# Load previous fix3 results
prev = json.load(open(os.path.join(ROOT, "fix3_results.json")))
to_retry = []
for name, info in prev.get("bad_request", []):
    to_retry.append(name)
for name in prev.get("no_fix", []):
    to_retry.append(name)
to_retry = sorted(set(to_retry))

print(f"to re-probe with smarter IDs: {len(to_retry)}", flush=True)
results = {"fixed": [], "rate_limited": [], "auth_required": [], "bad_request": [], "no_fix": [], "crash": []}
i = 0
for name in to_retry:
    i += 1
    q = build_query(name)
    if q is None:
        results["no_fix"].append(name)
        sys.stderr.write(f"[{i}/{len(to_retry)}] {name:50s} NO_FIX\n")
        sys.stderr.flush()
        continue
    status, _, elapsed, err = run_sql_capture(q, timeout=25)
    if status in ("data", "empty"):
        results["fixed"].append(name)
        emoji = "✅" if status == "data" else "∅"
        sys.stderr.write(f"[{i}/{len(to_retry)}] {name:50s} {emoji} {status} t={elapsed:.1f}s\n")
    elif status == "crash":
        results["crash"].append(name)
        sys.stderr.write(f"[{i}/{len(to_retry)}] {name:50s} 💥 CRASH\n")
    else:
        cat = classify_error(err or "")
        if cat == "rate_limited":
            results["rate_limited"].append(name)
            sys.stderr.write(f"[{i}/{len(to_retry)}] {name:50s} ⏱ RATE_LIMITED\n")
        elif cat == "auth_required":
            results["auth_required"].append(name)
            sys.stderr.write(f"[{i}/{len(to_retry)}] {name:50s} 🔒 AUTH\n")
        else:
            results["bad_request"].append((name, err))
            sys.stderr.write(f"[{i}/{len(to_retry)}] {name:50s} ❌ {cat} err={(err or '')[:80]}\n")
    sys.stderr.flush()
    if i % 10 == 0:
        json.dump(results, open(os.path.join(ROOT, "smart_results.json"), "w"), default=str, indent=2)

json.dump(results, open(os.path.join(ROOT, "smart_results.json"), "w"), default=str, indent=2)
print(f"\nDONE.")
for k, v in results.items():
    print(f"  {k}: {len(v)}")