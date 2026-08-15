"""
Build a probe SQL for each of the 364 github tables.

Heuristics:
- If no required filters: SELECT * LIMIT 1
- If owner + repo: use withcoral/coral
- If org: use withcoral
- If username: use FiscalMindset
- If enterprise: use withcoral
- If specific id (assignment_id, run_id, job_id, number, etc.):
    try with a sentinel '0' / '1' (these tables will return 0 rows or error)
- If multiple filters include owner+repo + an id, supply both
"""

import json, re, os

ROOT = "/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-full-test"
TABLES = json.load(open("/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-catalog/tables.json"))

DEFAULTS = {
    "owner": "withcoral",
    "repo": "coral",
    "org": "withcoral",
    "username": "FiscalMindset",
    "user": "FiscalMindset",
    "actor_id": "0",
    "actor_type": "User",
    "enterprise": "withcoral",
    "min_timestamp": "2020-01-01T00:00:00Z",
    "timestamp_increment": "day",
    "package_type": "npm",
    "package_name": "left-pad",
    "image_definition_id": "0",
    "team_slug": "engineering",
    "team_id": "0",
    "user_id": "0",
    "subject_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "plan_id": "0",
    "codespace_name": "test-codespace",
    "assignment_id": "0",
    "classroom_id": "0",
    "attempt_number": "1",
    "alert_number": "1",
    "check_run_id": "0",
    "check_suite_id": "0",
    "sarif_id": "0",
    "deployment_id": "0",
    "tag": "v1.0.0",
    "tag_sha": "0",
    "commit_sha": "0",
    "file_sha": "0",
    "tree_sha": "0",
    "issue_number": "1",
    "pull_number": "1",
    "review_id": "0",
    "branch": "main",
    "ref": "main",
    "head_sha": "0",
    "hook_id": "0",
    "export_id": "0",
    "asset_id": "0",
    "release_id": "0",
    "comment_id": "0",
    "thread_id": "0",
    "gist_id": "0",
    "sha": "0",
    "ruleset_id": "0",
    "pages_deployment_id": "0",
    "run_id": "0",
    "job_id": "0",
    "workflow_id": "0",
    "runner_id": "0",
    "runner_group_id": "0",
    "app_slug": "github",
    "path": "README.md",
    "configuration_id": "0",
    "codeql_variant_analysis_id": "0",
    "role_id": "0",
    "network_settings_id": "0",
    "installation_id": "0",
    "review_id": "0",
    "basehead": "main...main",
    "devcontainer_path": ".devcontainer/devcontainer.json",
    "day": "2024-01-01",
    "project_number": "0",
    "codeql_variant_analysis_id": "0",
    "environment_name": "production",
    "enterprise-team": "engineering",
}

def quote(v):
    return "'" + str(v).replace("'", "''") + "'"

def build_query(name):
    required = TABLES.get(name, {}).get("required_filters", [])
    seen = set()
    required = [f for f in required if not (f in seen or seen.add(f))]
    if not required:
        return f"SELECT * FROM github.{name} LIMIT 1"
    clauses = []
    for f in required:
        v = DEFAULTS.get(f)
        if v is None:
            v = "0"
        clauses.append(f"{f}={quote(v)}")
    return f"SELECT * FROM github.{name} WHERE " + " AND ".join(clauses) + " LIMIT 1"

if __name__ == "__main__":
    out = {}
    skipped = []
    for name in sorted(TABLES.keys()):
        try:
            q = build_query(name)
            out[name] = q
        except Exception as e:
            skipped.append((name, str(e)))
    with open(os.path.join(ROOT, "probes.json"), "w") as f:
        json.dump({"queries": out, "skipped": skipped, "total": len(out)}, f, indent=2)
    print(f"built {len(out)} probe queries")
    if skipped:
        print(f"skipped {len(skipped)}")
        for s in skipped[:5]:
            print(" ", s)
    # show a few samples
    for k in list(out.keys())[:3]:
        print("  ", k, "->", out[k][:120])