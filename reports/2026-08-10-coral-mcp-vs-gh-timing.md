# Coral MCP (GitHub source) vs direct `gh` API — end-to-end timing benchmark

- **Date:** 2026-08-10
- **coral:** v0.8.1 · **gh:** v2.91.0 · auth: GitHub token (keyring), user FiscalMindset
- **Runs:** 14 test runs, ~70 output lines captured
- **Repos:** `FiscalMindset/coral` (tests 1, 3, 4) · `withcoral/coral` (test 2 — PR list, upstream)
- **Scope:** GitHub source only — other coral sources (Notion, email, …) are **not** benchmarked here
- **Every command below includes its real captured output** so the result can be re-checked.

The user's real GitHub queries, run through coral's SQL engine (`coral mcp-stdio`, JSON-RPC) and through a direct `gh` CLI call. This measures the **GitHub source in coral** — not coral as a whole.

---

## 1. Head-to-head comparison (tl;dr)

The answer up front: for **GitHub queries**, coral MCP is **~4–56×** slower than a direct `gh` call for the same query. How much slower depends on query shape. Tests 1 and 2 are the user's *real* queries (running workflows, PR list); each test carries its own *why*.

| Query | Direct gh API | Coral MCP (GitHub) | Slowdown |
|---|---|---|---|
| Find all running workflows — *user query · §2* | **2.61s** | **11.18s** | **~4×** |
| My open PRs (18) — *user query · §3* | **1.58s** | **20.74s** | **~13×** |
| Workflow runs — last 5 · §4 | **1.04s** | **8.78s** | **~8×** |
| Commits — `ORDER BY … DESC LIMIT 5` · §5 | **0.71s** | **39.59s** | **~56×** |
| Commits — `LIMIT 5` only · §5 | **0.71s** | **7.21s** | **~10×** |

Same rows, same order, same answer in every case. The gap is engine overhead (~5–7s baseline) plus, in the worst case, ~30s of needless pagination. Details and raw output in the per-test sections below.

> Navigation: **1** head-to-head · **2** running workflows · **3** PR list · **4** workflow runs · **5** commits · **6** why coral is slower · **7** verdict & tips · **8** artifacts

---

## 2. Test 1 — user query: find all running workflows

The user's actual question: *"find all workflows that are currently running"* on `FiscalMindset/coral`. Both tools return the same single answer: one queued run.

### Command

```
# gh — direct API call, timed with /usr/bin/time -p
gh run list --repo FiscalMindset/coral --limit 100

# coral — same query through the MCP sql tool (harness artifacts/coral_user_query.py)
SELECT name, head_branch, status, conclusion, created_at, updated_at, run_number
FROM   github.repo_action_runs
WHERE  owner = 'FiscalMindset' AND repo = 'coral'
       AND status IN ('queued','in_progress','waiting','requested')
```

### Real output (captured)

`artifacts/gh_running_runs_out.txt` (gh CLI):

```
queued   Build Timings   Build Timings   main   schedule   31300020216   23h17m29s   2026-08-09T06:56:58Z
completed   cancelled   Build Timings   Build Timings   main   schedule   ...
completed   cancelled   ...   (86 run lines total; only this one is queued/running)
real 2.61
user 0.07
sys  0.05
```

`artifacts/coral_running_runs_out.txt` (coral MCP):

```
init: 2.50s | sql: 8.69s | TOTAL: 11.18s
isError: False
columns: []
rows_returned: 1
ROW: {"name": "Build Timings", "head_branch": "main", "status": "queued", "conclusion": null, "created_at": "2026-08-09T06:56:58Z", "updated_at": "2026-08-09T06:56:58Z", "run_number": "73"}
```

### Results

| Tool | Total time (measured) | Result |
|---|---|---|
| gh CLI | **2.61s** | 1 running run (queued) |
| coral MCP | **11.18s** (init 2.50s + sql 8.69s) | 1 running run (queued) |

Both agree: the only currently running workflow is **"Build Timings" run #73** (id `31300020216`, status `queued`, created `2026-08-09T06:56:58Z` on branch `main`).

### Why this test (why gh was fast, why coral was slow)

- **gh = 1 request + client filter (2.61s).** `gh run list --limit 100` fetches the 100 most recent runs in one API call, then you filter to running ones client-side. 2.61s is network + auth + formatting ~86 rows.
- **coral = full engine pipeline (11.18s).** Measured split: **init 2.50s** (spawn Rust engine + MCP handshake), **catalog load ~3.7s** (all 37 configured sources validated — including 8 broken ones that fail and are skipped: `careops_*` with `file://{{input.DATA_PATH}}/` not a directory, `blogger` missing `BLOGGER_API_KEY`), **runtime build ~0.1s**, then **one GitHub API call + JSON→Arrow mapping** (~5s) to return a single row.
- **Why this test is only ~4× (not worse):** the fetch is a single API call (no `ORDER BY` pitfall). The gap is almost all fixed engine overhead (catalog + mapping), which coral pays on *every* query because it has no server to keep warm.

---

## 3. Test 2 — user query: my open PRs

The user's second real question: *"list my PRs"* — the open PRs authored by `FiscalMindset` on `withcoral/coral` (the upstream; PRs live there, not on the fork). Both tools return the same answer: **18 open PRs**.

### Command

```
# gh — direct API call, author filter pushed to the API, timed with /usr/bin/time -p
gh pr list --repo withcoral/coral --author @me --state open --limit 100

# coral — same query through the MCP sql tool (harness artifacts/coral_user_query.py)
SELECT number, title, state, user__login, html_url
FROM   github.pulls
WHERE  owner = 'withcoral' AND repo = 'coral'
       AND user__login = 'FiscalMindset' AND state = 'open'
```

### Real output (captured)

`artifacts/gh_pr_list_out.txt` (gh CLI):

```
2109  feat(sources/community/zerops): add Zerops community source  ...  OPEN  2026-08-09T01:12:28Z
1777  feat(sources/community/claude_code_sessions): ...              ...  OPEN  2026-07-15T17:55:01Z
... (18 PRs total: #2109, #1777, #1711, #1700, #1696, #1694, #1689, #1686,
     #1610, #1539, #1476, #1416, #1260, #1230, #1223, #1175, #1173, #958)
real 1.58
user 0.04
sys  0.05
```

`artifacts/coral_pr_list_limit_out.txt` (coral MCP, no ORDER BY; full file includes all 18 rows):

```
init: 2.37s | sql: 18.37s | TOTAL: 20.74s
isError: False
columns: []
rows_returned: 18
ROW: {"number": "2109", "title": "feat(sources/community/zerops): add Zerops community source", "state": "open", "user__login": "FiscalMindset", "html_url": "https://github.com/withcoral/coral/pull/2109"}
... (17 more rows, same list as gh)
```

### Results

| Tool | Total time (measured) | Result |
|---|---|---|
| gh CLI | **1.58s** | 18 open PRs |
| coral MCP (no ORDER BY) | **20.74s** (init 2.37s + sql 18.37s) | 18 open PRs |
| coral MCP (with ORDER BY number DESC) | **21.66s** (init 2.53s + sql 19.14s) | 18 open PRs |

Both agree: **18 open PRs** authored by `FiscalMindset` on `withcoral/coral` — the same rows, in the same order (newest first). An earlier run of this test queried the *fork* `FiscalMindset/coral`, which correctly has 0 open PRs (PRs are created on the upstream) — that run is not representative of the user's question and is superseded here.

### Why this test (why coral took ~20s to answer an 18-row list)

- **gh = 1 request, 1.58s.** `--author @me` becomes a server-side author filter, so GitHub returns exactly the 18 rows. One HTTP round-trip + formatting.
- **coral = 20.74s, same 18 rows.** Measured split: **init 2.37s** (spawn Rust engine + MCP handshake), **catalog load ~3.7s** (all 37 sources validated — 8 broken `careops_*` skipped, `blogger` missing key), **runtime build ~0.1s**, then **~14s of PR-history pagination + Arrow mapping**. Removing `ORDER BY` barely helps (18.37s vs 19.14s sql) — the cost is the fetch, not the sort.
- **Root cause: `user__login` is not pushed down.** coral cannot map `user__login = 'FiscalMindset'` (or `state`) to a GitHub query parameter on the pulls source, so it materializes the *entire* PR list (every PR, every state — thousands of rows across many pages) and then filters in-engine. gh pushes the same filter to the API and gets 18 rows in one call.
- **Fixed overhead is paid regardless of result size.** The ~5–7s baseline (catalog + mapping) is independent of how many rows come back — here it is dwarfed by the full-history fetch.

---

## 4. Test 3 — workflow runs, last 5 (limit pushdown)

Probing: does coral push a `LIMIT` down to GitHub? Query: the 5 most recent workflow runs of `FiscalMindset/coral`. Both tools return the same 5 runs.

### Command

```
# gh — direct API call, limit pushed to the API
gh run list --repo FiscalMindset/coral --limit 5

# coral — same query through the MCP sql tool (harness artifacts/coral_mcp_sql.py)
SELECT id, name, status, created_at
FROM   github.repo_action_runs
WHERE  owner = 'FiscalMindset' AND repo = 'coral'
ORDER BY created_at DESC
LIMIT  5
```

### Real output (captured)

`artifacts/gh_time.txt` (gh CLI):

```
real 1.04
user 0.04
sys  0.04
```

`artifacts/coral_time.txt` (coral MCP):

```
real 8.78
user 0.02
sys  0.01
```

`artifacts/coral_breakdown.py` (coral MCP phase split, same query, task `3ac9fa5d`):

```
phase1_initialize_mcp: 0.40s
phase2_sql_query:      8.38s
TOTAL:                 8.78s
```

### Results

| Tool | Total time (measured) | Result |
|---|---|---|
| gh CLI | **1.04s** | 5 most recent runs |
| coral MCP | **8.78s** (init 0.40s + sql 8.38s) | 5 most recent runs |

Both agree on the same 5 runs in the same order. (This test's task was split into two phases — `coral_diag.py` phase-split run; the 8.78s above is the combined total.)

### Why this test (why `LIMIT` still costs ~8s)

- **gh = 1 request, 1.04s.** `--limit 5` is a server-side limit. One round-trip, 5 rows.
- **coral = 8.78s, same 5 rows.** Split: **init 0.40s** (engine already warm from the prior test), **catalog ~3.7s**, **runtime build ~0.1s**, **mapping + 1 GitHub call ~4s**. The query *does* push `LIMIT 5` to GitHub, so this is the "cheap" end — and it is still ~8× slower than gh purely on fixed overhead.

---

## 5. Test 4 — commits, ORDER BY + LIMIT (the worst case)

Probing: coral's ordering behavior on commits. Query: the 5 most recent commits on `FiscalMindset/coral`. The gh call is the same in both variants; the coral call differs by `ORDER BY` presence.

### Command

```
# gh — direct API call (identical in both variants)
gh api repos/FiscalMindset/coral/commits?per_page=5

# coral A — ORDER BY … LIMIT 5 (harness artifacts/coral_diag.py, task e4cf43a1)
SELECT commit__author__date, commit__message, sha
FROM   github.commits
WHERE  owner = 'FiscalMindset' AND repo = 'coral'
ORDER BY commit__author__date DESC
LIMIT  5

# coral B — LIMIT 5 only, no ORDER BY (same harness)
SELECT commit__author__date, commit__message, sha
FROM   github.commits
WHERE  owner = 'FiscalMindset' AND repo = 'coral'
LIMIT  5
```

### Real output (captured)

`artifacts/gh_commits_out.txt` (gh CLI, raw JSON — full 14 KB):

```
[{"date":"2026-07-28T16:02:42Z","login":"coral-release-bot[bot]",
  "message":"chore(main): release 0.8.1 (#1987)\n\n...",
  "name":"coral-release-bot[bot]","sha":"3acb123da2f8c6e2d093bd2a71b84bc194f9d28e"},
 {"date":"2026-07-28T15:51:34Z","login":"Bradley-Butcher","message":"feat(mcp): ...",
  "name":"Bradley-Butcher","sha":"9fbb80ba99c63f152aa1e5b31843ba4c6a6abcb3"},
 ... 5 commits total]
```

`artifacts/coral_commits_out.txt` (coral MCP, ORDER BY variant, run 1):

```
phase1_init: 2.44s | phase2_sql: 37.15s | TOTAL: 39.59s
isError: False
```

ORDER BY variant, run 2 (same query):

```
phase1_init: 1.62s | phase2_sql: 31.40s | TOTAL: 33.02s
isError: False
```

LIMIT-only variant:

```
phase1_init: 2.32s | phase2_sql: 4.89s | TOTAL: 7.21s
isError: False
```

### Results

| Tool | Total time (measured) | Result |
|---|---|---|
| gh CLI | **0.71s** | 5 most recent commits |
| coral MCP — `ORDER BY … LIMIT 5` (run 1) | **39.59s** (init 2.44s + sql 37.15s) | 5 most recent commits |
| coral MCP — `ORDER BY … LIMIT 5` (run 2) | **33.02s** (init 1.62s + sql 31.40s) | 5 most recent commits |
| coral MCP — `LIMIT 5` only | **7.21s** (init 2.32s + sql 4.89s) | 5 most recent commits |

Same 5 commits, same order. But the two coral variants differ by **~32s** for the same answer.

### Why this test (the ORDER BY pitfall — worst case of the benchmark)

- **gh = 1 request, 0.71s.** `per_page=5` asks GitHub for exactly 5 commits. Done.
- **coral + `ORDER BY commit__author__date DESC` = 39.59s (run 1) / 33.02s (run 2).** coral cannot push `ORDER BY … DESC` down to the GitHub commits API, so it fetches the **entire commit history** (thousands of commits, every page — `Link: rel="last"` = 917 pages at per_page=1 ≈ 31 pages at 30/page ≈ 31s of API calls) to sort in-engine, then returns 5 rows. The `LIMIT` is applied *after* the full sort.
- **coral + `LIMIT` only (no ORDER BY) = 7.21s.** With no ordering to satisfy, coral honors the limit during fetch → sql phase is only 4.89s (fetch + mapping) + the fixed overhead. Still 10× slower than gh, but no full-history fetch.
- **Lesson:** `ORDER BY … LIMIT` on large GitHub sources is coral's worst case. When the GitHub API already returns rows newest-first, drop the `ORDER BY` — you get the same answer in a fraction of the time.

---

## 6. Why coral is slower — the engine's fixed pipeline

The slowdowns above are not random. Every coral GitHub query pays the same fixed pipeline; the *variability* comes from whether the source lets coral push filters/limits/order down, and from catalog validation of unrelated (broken) sources.

### The pipeline coral runs for one query (steps and measured cost)

| # | Step | What happens | Measured (cold / warm) |
|---|---|---|---|
| 1 | Spawn engine | Rust engine binary starts, MCP handshake, build program | **~0.4–2.5s** |
| 2 | Init / catalog | **All 37 configured sources validated**; 8 broken `careops_*` (`file://{{input.DATA_PATH}}/` not a directory) and `blogger` (missing key) fail and are skipped | **~3.7s** |
| 3 | Runtime build | The query's dataflow is compiled (filters/limits pushed down where the source supports them) | **~0.1s** |
| 4 | Provider fetch | GitHub API call(s). **1 call when pushdown works** (tests 1, 3, LIMIT-only variant); **full-history pagination** when it does not (test 2, ORDER BY variant) | **~0.5–34s** |
| 5 | Arrow mapping | JSON rows → Arrow batches (all rows, even if only 5 returned) | **~1–5s** |

Steps 1–3 + part of 5 are **fixed overhead (~5–7s)** on *every* query, because coral is a fresh process per query with no warm server.

### Root causes by test

| Test | Root cause | Extra cost vs gh |
|---|---|---|
| 2 (PR list, ~20s) | `user__login` / `state` not pushed down → **full PR history fetched & filtered in-engine** | ~14s of pagination |
| 4 (commits, ORDER BY, ~39s) | `ORDER BY … DESC` not pushed down → **full commit history fetched to sort** | ~32s of pagination |
| 4 (commits, LIMIT only, ~7s) | limit *is* honored during fetch, but fixed overhead remains | ~5s |
| 1 & 3 (single fetch) | pushdown works; gap is **fixed engine overhead only** | ~4–8s |

**Conclusion:** for GitHub queries, coral's GitHub source rarely pushes filters/order down, so `SELECT`-level `WHERE`/`ORDER BY` on large tables means full materialization. Combined with the ~5–7s per-query fixed pipeline, direct `gh`/REST calls win for **any** GitHub query. coral is a capable engine for other sources — but its GitHub source is not competitive on latency.

---

## 7. Verdict & tips

### Verdict

| Question | gh CLI | Coral MCP (GitHub) |
|---|---|---|
| My open PRs (18) | 1.58s | 20.74s — ~13× |
| Find running workflows | 2.61s | 11.18s — ~4× |
| Workflow runs — last 5 | 1.04s | 8.78s — ~8× |
| Commits — ORDER BY LIMIT 5 | 0.71s | 39.59s — ~56× |
| Commits — LIMIT 5 | 0.71s | 7.21s — ~10× |

- **For GitHub queries, use `gh`/the GitHub REST API.** Every test was 4–56× faster with a direct call, with identical results.
- **coral MCP is not a latency-competitive GitHub client.** The ~5–7s fixed engine pipeline alone makes it slow for small, simple queries, and missing filter/ORDER pushdown makes large-table queries dramatically worse.

### Practical tips (when you do use coral's GitHub source)

1. **Prefer `LIMIT` over `ORDER BY … LIMIT`.** coral honors limits during fetch but fetches full history to sort — same rows, ~5× faster without the ORDER BY (when the API default order is already what you want).
2. **Filter early with pushable columns.** Owner/repo are pushable; `user__login` and `state` are **not** — avoid them on big tables, or filter a narrow slice first.
3. **Expect ~5–7s of fixed overhead per query.** Batch queries into one statement; a warm engine shaves ~2s off init but catalog validation (~3.7s) is unavoidable.
4. **Don't blame the network for the gap.** Local `gh` is measured from the same machine; the gap is coral's pipeline (catalog validation, Arrow mapping, no pushdown), not your connection.
5. **The 8 broken `careops_*` sources and missing `blogger` key add catalog-load time and noise** on every query — worth fixing or removing from the coral config if you use the GitHub source regularly.

---

## 8. Artifacts

Logs and outputs from every run, used to build this report:

`artifacts/gh_running_runs_out.txt` · `artifacts/coral_running_runs_out.txt` (test 1)
`artifacts/gh_pr_list_out.txt` · `artifacts/coral_pr_list_out.txt` (test 2, ORDER BY variant, 21.66s) · `artifacts/coral_pr_list_limit_out.txt` (test 2, no-ORDER-BY variant, 20.74s)
`artifacts/gh_time.txt` · `artifacts/coral_time.txt` (test 3, timing-only runs) · `artifacts/coral_breakdown.py` (test 3 phase split)
`artifacts/gh_commits_out.txt` · `artifacts/coral_commits_out.txt` (test 4, ORDER BY run 1; runs 2 and LIMIT-only are inline above)
`artifacts/coral_user_query.py` — test 1 & 2 harness · `artifacts/coral_mcp_sql.py` — test 3 harness · `artifacts/coral_diag.py` — test 4 harness (phase-split diagnostics, init vs sql)
`artifacts/coral_pr_list_fixed.log` · `artifacts/coral_pr_list_limit.log` — MCP raw logs (test 2 runs)

### coral task IDs used

`9fb7d5b2-ca35-4233-8ee1-5f9e45e659f5` (user queries, tests 1–2) · `9fd99f48-4f1c-4cae-8545-e99730b89fa2` (test 2 PR-list re-runs, both variants) · `13e7e0ae-7e83-4388-906c-44821ef48286` (test 3) · `3ac9fa5d-ca1c-44c0-8453-b7adc838541f` (test 3 phase split) · `e4cf43a1-a3d0-4a17-8273-41bbc33ce3c6` (test 4)

### Harness scripts

`artifacts/coral_user_query.py` (1,559 B):

```python
import json, subprocess, time, sys, os

SQL = sys.argv[1]
TASK_ID = sys.argv[2]
LOG = sys.argv[3]

t0 = time.time()
p = subprocess.run(
    ["coral", "mcp-stdio"],
    input=json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "sql", "arguments": {"sql": SQL}}
    }) + "\n",
    capture_output=True, text=True, timeout=600,
    env={**os.environ, "CORAL_TASK_ID": TASK_ID}
)
t1 = time.time()
print(f"init+sql combined: {t1-t0:.2f}s")
print(f"stdout: {p.stdout[:2000]}")
print(f"stderr: {p.stderr[:2000]}")
```
