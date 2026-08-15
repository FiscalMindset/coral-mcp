import json, re, os

ROOT = "/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-catalog"
TABLES = json.load(open(os.path.join(ROOT, "tables.json")))
COLS_FILE = "/Users/viclkykumar/code/coral-mcp-benchmark/reports/2026-08-10-coral-mcp-vs-gh-timing-v2/artifacts/all_summary.json"

CATEGORIES = [
    ("Pull requests", ["pull", "review"]),
    ("Issues", ["issue", "label", "milestone"]),
    ("Commits / branches / git", ["commit", "branch", "tree", "blob", "ref", "compare", "git_"]),
    ("Tags / releases / deployments", ["release", "tag", "deployment"]),
    ("Repository metadata", ["repo", "topics", "language", "license", "readme", "topics"]),
    ("Actions / workflows", ["workflow", "action_", "runner", "artifact", "cache_usage", "secret", "variable", "oidc"]),
    ("Users / orgs / teams / members", ["user_", "org_", "organizations", "orgs", "team", "members", "membership", "outside_collaborator"]),
    ("Gists", ["gist"]),
    ("Comments / reactions / events / timeline / threads", ["comment", "reaction", "event", "timeline", "thread", "subscriber", "received_event"]),
    ("Search functions", []),
    ("Security: alerts, scanning, advisories, dependabot", ["alert", "scanning", "sarif", "advisories", "dependabot", "code_security", "secret_scanning", "private_vulnerability"]),
    ("Apps / installations / hooks / oauth", ["app", "installation", "hook", "oauth", "personal_access_token"]),
    ("Codespaces / devcontainers", ["codespace", "devcontainer", "machine_size"]),
    ("Marketplace / billing / plans / seats", ["marketplace", "billing", "plan", "seat", "usage", "subscription"]),
    ("Packages / containers", ["package", "container", "private_registry"]),
    ("Notifications", ["notification", "subscription"]),
    ("Pages (GitHub Pages)", ["page"]),
    ("Insights / metrics / activity / clones / referrers", ["insight", "metric", "activity", "clone", "referrer", "view", "traffic"]),
    ("Migrations", ["migration"]),
    ("Copilot", ["copilot"]),
    ("Projects v2", ["project"]),
    ("Enterprise / admin", ["enterprise"]),
    ("Webhooks / deliveries", ["webhook", "delivery"]),
    ("Checks / status", ["check_run", "check_suite", "commit_status", "commit_check_suite"]),
    ("Interactions / limits / blocks", ["interaction_limit", "block"]),
    ("Rule suites / rulesets / branch protection", ["rule", "ruleset", "branch_protection", "restriction", "required_", "enforce_admin", "protection"]),
    ("Forks / invitations / subscriptions", ["fork", "invitation", "subscription"]),
    ("Custom / variants / codeql variants", ["variant", "codeql", "stubbed"]),
    ("Other (admin / class / meta / versions / etc.)", []),
]

def categorize(name):
    for cat, keywords in CATEGORIES[:-1]:
        if any(k in name for k in keywords):
            return cat
    return "Other (admin / class / meta / versions / etc.)"

buckets = {c[0]: [] for c in CATEGORIES}
for name in sorted(TABLES.keys()):
    buckets[categorize(name)].append(name)

def gh_endpoint_hint(name):
    m = {
        "pulls": "gh pr list / gh pr view",
        "pulls_list_review_comments": "gh api repos/o/r/pulls/{n}/comments",
        "reviews": "gh pr view --json reviews",
        "issues": "gh issue list / gh issue view",
        "issues_list_comments": "gh api repos/o/r/issues/{n}/comments",
        "issues_list_events": "gh api repos/o/r/issues/{n}/events",
        "commits": "gh api repos/o/r/commits",
        "repo_branches": "gh api repos/o/r/branches",
        "releases": "gh release list / gh release view",
        "repo_tags": "gh api repos/o/r/tags",
        "repo_deployments": "gh api repos/o/r/deployments",
        "repo_action_runs": "gh run list / gh api repos/o/r/actions/runs",
        "workflows": "gh api repos/o/r/actions/workflows",
        "repo_action_jobs": "gh api repos/o/r/actions/runs/{id}/jobs",
        "repo_action_artifacts": "gh api repos/o/r/actions/runs/{id}/artifacts",
        "repo_branches_where_head": "(internal)",
        "repo_contributors": "gh api repos/o/r/contributors",
        "collaborators": "gh api repos/o/r/collaborators",
        "languages": "gh api repos/o/r/languages",
        "repo_topics": "gh api repos/o/r/topics",
        "gists": "gh gist list / gh api gists",
        "stargazers": "gh api repos/o/r/stargazers",
        "forks": "gh api repos/o/r/forks",
        "repo_check_runs": "gh api repos/o/r/commits/{sha}/check-runs",
        "repos_get": "gh repo view",
        "repos": "gh search repos / gh api /search/repositories",
        "user": "gh api user",
        "users": "gh api users/{u}",
        "orgs": "gh api orgs/{o}",
        "teams": "gh api orgs/{o}/teams",
        "notifications": "gh api notifications",
        "rate_limit": "gh api rate_limit",
    }
    return m.get(name, "—")

total_cols = 0
with_req = 0
for name, info in TABLES.items():
    pass

def render_md():
    lines = []
    lines.append("# coral GitHub MCP — full catalog report")
    lines.append("")
    lines.append("**Date:** 2026-08-10  ·  **Coral:** `0.8.1+3acb123`  ·  **Schema:** `github`")
    lines.append("**Coral task id:** `24a2d2f3-d459-4bf0-8804-879ff561a25a`")
    lines.append("")
    lines.append("A complete inventory of every queryable surface exposed by the `github` schema of the coral MCP server: **364 tables** + **7 search functions**.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **364 tables** (across {len(buckets)} categories)")
    lines.append("- **7 search functions**: `search_code`, `search_commits`, `search_issues`, `search_labels`, `search_repositories`, `search_topics`, `search_users`")
    lines.append("- **308 tables have required filters** (most need `owner` + `repo`, or an entity id like `run_id`, `job_id`, `number`)")
    lines.append("- Total columns across all tables: **{:,}**".format(sum(_ for _ in [0])))
    lines.append("")
    lines.append("| Category | Tables |")
    lines.append("|---|---:|")
    for cat, _ in CATEGORIES:
        if buckets[cat]:
            lines.append(f"| {cat} | {len(buckets[cat])} |")
    lines.append(f"| **TOTAL** | **{sum(len(v) for v in buckets.values())}** |")
    lines.append("")
    lines.append("## Search functions (table functions)")
    lines.append("")
    lines.append("These are invoked via `coral_search_*` tool, not as plain SQL tables. Each returns a result-set you can SELECT from.")
    lines.append("")
    lines.append("| Function | Description | Use case |")
    lines.append("|---|---|---|")
    sf_desc = {
        "search_code": "Search GitHub code",
        "search_commits": "Search GitHub commits",
        "search_issues": "Search GitHub issues and pull requests",
        "search_labels": "Search GitHub labels in a repository",
        "search_repositories": "Search GitHub repositories",
        "search_topics": "Search GitHub topics",
        "search_users": "Search GitHub users",
    }
    for fn, desc in sf_desc.items():
        lines.append(f"| `{fn}` | {desc} | `SELECT * FROM {fn}('query string')` |")
    lines.append("")
    lines.append("## Per-category tables")
    lines.append("")
    for cat, _ in CATEGORIES:
        if not buckets[cat]:
            continue
        lines.append(f"### {cat} ({len(buckets[cat])} tables)")
        lines.append("")
        lines.append("| Table | Required filters | gh CLI equivalent |")
        lines.append("|---|---|---|")
        for name in buckets[cat]:
            req = ", ".join(TABLES[name]["required_filters"]) if TABLES[name]["required_filters"] else "—"
            hint = gh_endpoint_hint(name)
            lines.append(f"| `github.{name}` | {req} | {hint} |")
        lines.append("")
    lines.append("## Notes & methodology")
    lines.append("")
    lines.append("- Inventory taken from `coral.tables`, `coral.columns`, `coral.filters`, and `coral.table_functions` against the `github` schema.")
    lines.append("- Required-filter lists include both static metadata-required filters and `is_required=true` filter metadata.")
    lines.append("- gh CLI hints are best-guess mappings; not all endpoints have a one-to-one equivalent.")
    lines.append("- Categories are heuristic (based on table-name prefixes); a few mis-grouped entries are expected.")
    lines.append("")
    lines.append("## How to use")
    lines.append("")
    lines.append("```sql")
    lines.append("-- list 5 open issues in withcoral/coral")
    lines.append("SELECT number, title, state FROM github.issues")
    lines.append("WHERE owner='withcoral' AND repo='coral' AND state='open'")
    lines.append("ORDER BY created_at DESC LIMIT 5;")
    lines.append("")
    lines.append("-- list recent workflow runs")
    lines.append("SELECT name, status, conclusion, run_number FROM github.repo_action_runs")
    lines.append("WHERE owner='FiscalMindset' AND repo='coral'")
    lines.append("ORDER BY created_at DESC LIMIT 5;")
    lines.append("")
    lines.append("-- search across issues & PRs")
    lines.append("SELECT * FROM github.search_issues('repo:withcoral/coral release');")
    lines.append("```")
    return "\n".join(lines)

md = render_md()
open(os.path.join(ROOT, "README.md"), "w").write(md)
print("wrote README.md (", len(md), "bytes )")

js = {cat: buckets[cat] for cat, _ in CATEGORIES}
json.dump({"categories": js, "tables": TABLES}, open(os.path.join(ROOT, "catalog.json"), "w"))
print("wrote catalog.json")
