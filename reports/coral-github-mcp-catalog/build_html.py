import json, os, html, re

ROOT = "/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-catalog"
data = json.load(open(os.path.join(ROOT, "catalog.json")))
cats = data["categories"]
tables = data["tables"]

CATEGORY_ORDER = [
    "Pull requests",
    "Issues",
    "Commits / branches / git",
    "Tags / releases / deployments",
    "Repository metadata",
    "Actions / workflows",
    "Users / orgs / teams / members",
    "Gists",
    "Comments / reactions / events / timeline / threads",
    "Search functions",
    "Security: alerts, scanning, advisories, dependabot",
    "Apps / installations / hooks / oauth",
    "Codespaces / devcontainers",
    "Marketplace / billing / plans / seats",
    "Packages / containers",
    "Notifications",
    "Pages (GitHub Pages)",
    "Insights / metrics / activity / clones / referrers",
    "Migrations",
    "Copilot",
    "Projects v2",
    "Enterprise / admin",
    "Webhooks / deliveries",
    "Checks / status",
    "Interactions / limits / blocks",
    "Rule suites / rulesets / branch protection",
    "Forks / invitations / subscriptions",
    "Custom / variants / codeql variants",
    "Other (admin / class / meta / versions / etc.)",
]

def gh_hint(name):
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
        "repo_contributors": "gh api repos/o/r/contributors",
        "collaborators": "gh api repos/o/r/collaborators",
        "languages": "gh api repos/o/r/languages",
        "repo_topics": "gh api repos/o/r/topics",
        "gists": "gh gist list / gh api gists",
        "stargazers": "gh api repos/o/r/stargazers",
        "repos_get": "gh repo view",
        "repos": "gh search repos",
        "user": "gh api user",
        "orgs": "gh api orgs/{o}",
        "teams": "gh api orgs/{o}/teams",
        "notifications": "gh api notifications",
        "rate_limit": "gh api rate_limit",
    }
    return m.get(name, "—")

SEARCH_FNS = {
    "search_code": "Search GitHub code.",
    "search_commits": "Search GitHub commits.",
    "search_issues": "Search GitHub issues and pull requests.",
    "search_labels": "Search GitHub labels in a repository.",
    "search_repositories": "Search GitHub repositories.",
    "search_topics": "Search GitHub topics.",
    "search_users": "Search GitHub users.",
}

def esc(s):
    return html.escape(s) if s else ""

parts = []
parts.append("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>coral GitHub MCP — full catalog</title>
<style>
:root{--fg:#1a1a1a;--mut:#6b7280;--bg:#fff;--soft:#f5f5f7;--line:#e5e7eb;--mono:ui-monospace,SFMono-Regular,Menlo,monospace}
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:var(--fg);background:var(--bg);max-width:1280px;margin:32px auto;padding:0 24px;line-height:1.5;font-size:14px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-0.02em}
h2{font-size:19px;margin:36px 0 12px;border-bottom:1px solid var(--line);padding-bottom:6px}
h3{font-size:15px;margin:18px 0 6px;color:#444;font-family:var(--mono)}
.meta{color:var(--mut);font-size:13px;margin-bottom:24px}
.meta code{font-size:12px}
.kpi{display:flex;gap:10px;margin:16px 0 8px;flex-wrap:wrap}
.kpi>div{flex:1;min-width:160px;background:var(--soft);padding:12px 14px;border-radius:10px;border:1px solid var(--line)}
.kpi .k{font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:var(--mut);font-weight:600}
.kpi .v{font-family:var(--mono);font-size:22px;font-weight:600;margin:4px 0;color:var(--fg)}
.kpi .n{font-size:12px;color:var(--mut)}
table{width:100%;border-collapse:collapse;margin:8px 0 18px;font-size:12.5px}
th,td{padding:5px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;color:#374151;position:sticky;top:0;z-index:1}
td.tnum,th.tnum{font-family:var(--mono);text-align:right}
td.mono{font-family:var(--mono);font-size:11.5px}
tr:hover td{background:#fafafa}
code{font-family:var(--mono);font-size:12px;background:#f3f4f6;padding:1px 5px;border-radius:3px}
.cat-card{border:1px solid var(--line);border-radius:8px;margin:10px 0;background:#fff;overflow:hidden}
.cat-card>summary{padding:10px 14px;cursor:pointer;font-weight:600;font-size:14px;background:var(--soft);list-style:none;display:flex;justify-content:space-between;align-items:center}
.cat-card>summary::before{content:'▸';margin-right:8px;color:var(--mut);transition:transform .15s;display:inline-block}
.cat-card[open]>summary::before{transform:rotate(90deg)}
.cat-card>summary .count{background:#e5e7eb;color:#374151;font-family:var(--mono);font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600}
.cat-card>div{padding:6px 14px 14px}
.toc{background:var(--soft);border:1px solid var(--line);border-radius:8px;padding:12px 16px;font-size:13px;margin:16px 0}
.toc a{color:#1f2937;text-decoration:none;display:inline-block;margin:3px 8px 3px 0;padding:3px 8px;background:#fff;border:1px solid var(--line);border-radius:6px;font-size:12px}
.toc a:hover{background:#e5e7eb}
input.search{width:100%;padding:10px 14px;border:1px solid var(--line);border-radius:8px;font-family:var(--mono);font-size:13px;margin:6px 0}
input.search:focus{outline:2px solid #93c5fd;outline-offset:1px}
mark{background:#fde68a;padding:0 2px;border-radius:2px}
tr.hidden{display:none}
.cat-card.hidden{display:none}
</style>
</head>
<body>
<h1>coral GitHub MCP — full catalog</h1>
<p class="meta">2026-08-10 · coral <code>0.8.1+3acb123</code> · schema <code>github</code> · task <code>24a2d2f3-d459-4bf0-8804-879ff561a25a</code></p>

<div class="kpi">
  <div><div class="k">Tables</div><div class="v">364</div><div class="n">across 29 categories</div></div>
  <div><div class="k">Search functions</div><div class="v">7</div><div class="n">table functions (not SQL tables)</div></div>
  <div><div class="k">Tables with required filters</div><div class="v">308</div><div class="n">84% of catalog</div></div>
  <div><div class="k">Largest table</div><div class="v" style="font-size:14px">repos_get</div><div class="n">564 columns</div></div>
</div>

<input class="search" id="search" placeholder="Filter tables (e.g. workflow, pr, search, gist) …" autocomplete="off">

<nav class="toc" id="toc"></nav>

<h2>Search functions (table functions)</h2>
<table>
  <thead><tr><th>Function</th><th>Description</th><th>Example SQL</th></tr></thead>
  <tbody>
""")

for fn, desc in SEARCH_FNS.items():
    parts.append(f'<tr><td><code>{fn}</code></td><td>{esc(desc)}</td><td><code>SELECT * FROM github.{fn}(&apos;repo:withcoral/coral release&apos;)</code></td></tr>')

parts.append("""
  </tbody>
</table>
<h2>Per-category tables</h2>
""")

toc_parts = []
for cat in CATEGORY_ORDER:
    if cat == "Search functions":
        continue
    items = cats.get(cat, [])
    if not items:
        continue
    cid = "cat-" + re.sub(r"[^a-z0-9]+", "-", cat.lower()).strip("-")
    toc_parts.append(f'<a href="#{cid}" data-cat="{esc(cat)}">{esc(cat)} <span class="count">{len(items)}</span></a>')

parts.append(f'<nav class="toc" id="toc-2">{"".join(toc_parts)}</nav>\n')

import re
for cat in CATEGORY_ORDER:
    if cat == "Search functions":
        continue
    items = cats.get(cat, [])
    if not items:
        continue
    cid = "cat-" + re.sub(r"[^a-z0-9]+", "-", cat.lower()).strip("-")
    parts.append(f'<details class="cat-card" id="{cid}" data-cat="{esc(cat)}"><summary>{esc(cat)}<span class="count">{len(items)} tables</span></summary><div>')
    parts.append('<table>')
    parts.append('<thead><tr><th>Table</th><th>Required filters</th><th>Description</th><th>gh CLI hint</th></tr></thead><tbody>')
    for name in items:
        info = tables.get(name, {"description":"", "required_filters":[]})
        req = ", ".join(info["required_filters"]) if info["required_filters"] else "—"
        desc = info["description"] or "—"
        hint = gh_hint(name)
        parts.append(f'<tr data-name="{esc(name)}"><td class="mono"><code>github.{esc(name)}</code></td><td class="mono">{esc(req)}</td><td>{esc(desc)}</td><td>{esc(hint)}</td></tr>')
    parts.append('</tbody></table></div></details>')

parts.append("""
<h2>Notes & methodology</h2>
<ul>
  <li>Inventory taken from <code>coral.tables</code>, <code>coral.columns</code>, <code>coral.filters</code>, and <code>coral.table_functions</code> against the <code>github</code> schema.</li>
  <li>Required-filter lists include both the static <code>required_filters</code> JSON column on <code>coral.tables</code> and <code>is_required=true</code> rows from <code>coral.filters</code>.</li>
  <li>gh CLI hints are best-guess mappings; not all endpoints have a one-to-one equivalent.</li>
  <li>Categories are heuristic (based on table-name prefixes); a few mis-grouped entries are expected. Use the filter box above to find specific tables.</li>
</ul>

<h2>How to use</h2>
<pre><code>-- list 5 open issues in withcoral/coral
SELECT number, title, state FROM github.issues
WHERE owner='withcoral' AND repo='coral' AND state='open'
ORDER BY created_at DESC LIMIT 5;

-- list recent workflow runs
SELECT name, status, conclusion, run_number FROM github.repo_action_runs
WHERE owner='FiscalMindset' AND repo='coral'
ORDER BY created_at DESC LIMIT 5;

-- search across issues &amp; PRs
SELECT * FROM github.search_issues('repo:withcoral/coral release');</code></pre>

<script>
const search = document.getElementById('search');
const rows = Array.from(document.querySelectorAll('tr[data-name]'));
const cards = Array.from(document.querySelectorAll('details.cat-card'));
function apply() {
  const q = search.value.trim().toLowerCase();
  rows.forEach(r => {
    const name = r.dataset.name.toLowerCase();
    if (!q || name.includes(q)) r.classList.remove('hidden');
    else r.classList.add('hidden');
  });
  cards.forEach(c => {
    const t = c.querySelectorAll('tr[data-name]');
    const visible = Array.from(t).filter(r => !r.classList.contains('hidden'));
    c.style.display = visible.length ? '' : 'none';
    if (!q) c.open = false;
    else c.open = true;
  });
  if (q) {
    cards.forEach(c => c.open = true);
  }
}
search.addEventListener('input', apply);
</script>
</body>
</html>
""")

html_text = "".join(parts)
open(os.path.join(ROOT, "index.html"), "w").write(html_text)
print("wrote index.html (", len(html_text), "bytes )")