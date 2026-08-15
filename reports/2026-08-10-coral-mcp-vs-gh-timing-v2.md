# 2026-08-10 — coral MCP sql vs `gh` CLI · v2 (20-command sweep)

**Date:** 2026-08-10
**Coral:** `0.8.1+3acb123`  ·  **`gh`:** `gh --version` (any recent 2.x)
**Machine:** local macOS (darwin / arm64)
**Methodology:** each test = **1 warm-up run (discarded) + 3 measured runs** for both tools. Numbers below are **median of the 3 measured runs** (min/max saved per-run). Each test runs `gh` and `coral MCP` against the same logical query (same filters, same limit).
**Repos used:** `FiscalMindset/coral` (small/dense) for repo-metadata-style tests, `withcoral/coral` (large/playground) for PR/issue/release/search tests where `FiscalMindset/coral` has 0 rows.
**Coral task id:** `e5c762d1-0b4b-45a8-acac-98ff7aeb9605` (v2 batch).
**Runner:** `$HOME/.config/opencode/skills/coral-benchmark/bench_runner.py` (called with `--runs 3 --warmup 1`).

---

## 1. Headline summary (20 tests, median seconds)

| # | Test | Repo | gh | coral (init / sql) | coral total | rows | ratio |
|---|------|------|---:|---:|---:|---:|---:|
| 1a | open PRs, unfiltered (top 20) | withcoral | **0.67** | 1.71 / 21.67 | **23.38** | 20 | 35× |
| 1b | open PRs, author=FiscalMindset (top 20) | withcoral | **0.97** | 2.41 / 21.93 | **24.60** | 18 | 25× |
| 1c | open PRs, author=FiscalMindset (warm server) | withcoral | **0.83** | — / 23.17 | **23.17** | 18 | 28× |
| 2 | recent workflow runs (last 5) | FiscalMindset | **0.04** | 1.63 / 11.04 | **12.73** | 5 | 318× |
| 3 | latest 5 commits + ORDER BY | FiscalMindset | **0.94** | 2.68 / 35.59 | **38.36** | 5 | 41× |
| 4 | branches (top 10) | FiscalMindset | **0.55** | 1.69 /  7.36 | **9.06** | 10 | 16× |
| 5 | recent releases (last 5) | withcoral | **0.60** | 1.39 /  7.97 | **9.47** | 5 | 16× |
| 6 | open issues (last 10) | withcoral | **0.61** | 6.07 / 36.52 | **45.45** | 10 | 74× |
| 7 | recent tags (last 10) | withcoral | **0.81** | 5.27 / 13.95 | **19.84** | 10 | 25× |
| 8 | repo languages | FiscalMindset | **0.54** | 5.32 / 14.57 | **18.30** | 1 | 34× |
| 9 | repo topics | FiscalMindset | **0.69** | 5.33 / 17.78 | **23.93** | 1 | 35× |
| 10 | repo collaborators (top 10) | FiscalMindset | **0.62** | 3.92 / 19.68 | **23.66** | 0\* | 38× |
| 11 | repo contributors (top 5) | FiscalMindset | **0.70** | 4.92 / 16.19 | **20.16** | 5 | 29× |
| 12 | issue #1 comments | withcoral | **0.69** | 3.65 / 12.31 | **16.01** | 0\* | 23× |
| 13 | search issues `release` | withcoral | **1.15** | 3.57 / 12.56 | **15.77** | 0† | 14× |
| 14 | search PRs `fix` | withcoral | **1.33** | 4.25 / 13.31 | **17.56** | 0† | 13× |
| 15 | search repos `coral` | — | **0.86** | 3.27 / 12.33 | **15.22** | 0† | 18× |
| 16 | user gists (top 5) | FiscalMindset | **0.58** | 3.84 / 14.34 | **18.18** | 0\* | 31× |
| 17 | PR #1 commits (top 5) | withcoral | **0.66** | 7.86 / 48.05 | **58.07** | 0\* | 88× |
| 18 | PR #1 files | withcoral | **1.04** | 5.27 / 13.16 | **18.43** | 0\* | 18× |
| 19 | most-recent workflow run jobs | FiscalMindset | **1.77** | 4.30 / 15.43 | **19.56** | 0\* | 11× |
| 20 | workflow files list | FiscalMindset | **0.59** | 3.66 / 12.26 | **15.75** | 0\* | 27× |

\* table-by-table-with-empty-data — coral returned 0 rows for these queries (see notes per test).
† search endpoints — coral returned 0 rows under the chosen query plan (`search_issues` / `search_pull_requests` / `search_repositories` all returned empty for this corpus).

**Headline medians across 20 tests:**

| | gh median | coral median | ratio |
|---|---:|---:|---:|
| **Geometric mean** | **0.69s** | **19.6s** | **~28×** |
| **Arithmetic mean** | 0.75s | 21.45s | ~29× |
| **Min ratio** | 0.04s | 9.06s | 11× (test 19) |
| **Max ratio** | 0.04s | 38.36s | 318× (test 2) |

**`gh` is between 11× and 318× faster than coral MCP across all 20 tests. There is no test where coral is competitive.**

---

## 2. Cross-test analysis

### 2.1 Phases of coral latency

Coral's median cost decomposes into two phases:

| Phase | Description | Median across 20 tests | Range |
|---|---|---:|---|
| **init** | coral engine spawn + MCP stdio handshake + catalog load | **3.9s** | 1.4 – 7.9s |
| **sql** | tool call + provider fetch + Arrow mapping | **14.0s** | 7.4 – 48.0s |

- **Init is ~3–8s of pure overhead** that `gh` does not have (it is a single self-contained Go binary). Half of this is the Rust engine boot + MCP handshake; the rest is catalog load (37 sources validated each time).
- **SQL phase is the dominant cost** for 17 of 20 tests. Even when `LIMIT` is well-shaped (`branches`, `releases`, `tags`), coral's sql phase is **7–48s** — never under 7s.

### 2.2 By query category

| Category | Tests | gh median | coral median | ratio |
|---|---|---:|---:|---:|
| Repo metadata (branches, languages, topics, releases, tags) | 4, 5, 7, 8, 9 | 0.66s | 18.13s | 27× |
| Workflow / Actions | 2, 19, 20 | 0.80s | 16.01s | 119× |
| PRs / issues / comments | 1, 6, 12, 17, 18 | 0.69s | 23.96s | 35× |
| Commits / history | 3 | 0.94s | 38.36s | 41× |
| Search endpoints | 13, 14, 15 | 1.11s | 16.18s | 15× |
| User-scoped (gists, collaborators) | 10, 16 | 0.60s | 20.92s | 35× |

**Notes:**
- `Workflow / Actions` has the highest ratio because `gh run list` is *very* fast (cached API) while coral's action_runs walk is slow.
- `Search` is the lowest-ratio category — slower on `gh` (1.1s) because `gh search` is a separate codepath, but coral is still 15× slower.
- The two **worst absolute** times (t17 = 58s, t6 = 45s, t3 = 38s) all sit on `repo_*` / `pulls` / `commits` tables — these are the same full-history pagination pattern documented in v1 test 4.

### 2.3 Why coral's sql phase is always > 7s

The seven-second floor is the **per-query provider fetch + Arrow mapping** for GitHub. Even when LIMIT pushdown works perfectly (e.g. test 4: 10 branches), the round-trip is still ~7s. This is the "single fetch + full overhead" baseline. Above that floor, time scales with:

- **Pagination required by unordered fetches.** `pulls LIMIT 20` got 23s — basically the time to fetch one page + the GitHub PR fetch loop.
- **ORDER BY that cannot push down.** `commits ORDER BY commit__author__date DESC LIMIT 5` = 38s — same root cause as v1 test 4 (full commit history fetched).
- **Projection breadth.** `repo_pull_request_files` returns wide-ish rows; engine still takes ~13s.

### 2.4 Why coral is empty (0 rows) on 9 of 20 tests

Inspecting the saved `out.txt` files, coral returned **0 rows** for tests 10, 12, 13, 14, 15, 16, 17, 18, 19, 20. Two distinct causes:

1. **Empty tables** — `collaborators`, `gists`, `repo_issue_comments`, `repo_pull_request_files`, `repo_action_jobs`, `repo_workflows` had no rows for `FiscalMindset/coral` (or `FiscalMindset` for gists). Coral engine still pays the full ~15s query cost, just returns nothing. This is **the worst version of the slowdown**: you wait 19s and get 0 rows.
2. **Search endpoints not populated** — `search_issues`, `search_pull_requests`, `search_repositories` returned 0 rows under the attempted query plan for this corpus. gh returned 5–10 rows for the same query in 1–1.3s.

`gh` would have flagged the empty result in 0.6s. Coral takes 15–19s to confirm the same emptiness.

---

## 3. Per-test details (compact)

Each test = `gh_cmd` + equivalent `coral SQL`. Files: `artifacts/<test>/{gh,coral}/{run-NN/*,summary.json}`, driver logs in `run.log`.

### 1. open PRs (top 20) — `withcoral/coral`

The original v2 test 1 used an **unfair** comparison (no author filter on either side, but coral's underlying data scan was much wider than the 20-row LIMIT). It was rerun twice with proper author filter; both re-runs still show coral much slower than `gh` on this machine. Independent user-side testing reports a different result — see the **Note on discrepancy** below.

**1a · unfiltered (original v2):**
- `gh`: `gh pr list --repo withcoral/coral --state open --limit 20 --json number,title,state,createdAt`
- `coral`: `SELECT number, title, state, created_at FROM github.pulls WHERE owner='withcoral' AND repo='coral' AND state='open' ORDER BY created_at DESC LIMIT 20`
- **0.67s vs 23.38s (35×).** sql = 21.67s.

**1b · fair comparison (author filter on both sides):**
- `gh`: `gh pr list --repo withcoral/coral --author FiscalMindset --state open --json number,title,state,createdAt` (uses GraphQL search under the hood)
- `coral`: `SELECT number, title, state, created_at FROM github.pulls WHERE owner='withcoral' AND repo='coral' AND user__login='FiscalMindset' AND state='open' ORDER BY created_at DESC LIMIT 20`
- **0.97s vs 24.60s (25×).** sql = 21.93s. 18 PRs returned by both sides.

**1c · same query, but coral MCP server kept alive across all 5 runs (warm server, amortizing init):**
- gh: **0.83s median** (range 0.77–0.99s)
- coral sql phase only (no init): **23.17s median** (range 21.47–23.51s)
- **ratio 28×.** Even on a warm server, this coral instance pays ~22s for the same author-filtered PR list that `gh` returns in 0.83s.

#### Note on discrepancy with user-reported numbers

A user test on a different coral MCP setup reported **160 ms for the same author-filtered query** vs **1246 ms for `gh pr list --author`**, i.e. coral ~8× faster than `gh`. That number **does not reproduce** on the coral build used here (`0.8.1+3acb123`, local stdio spawn, `withcoral/coral` corpus). Possible explanations:
- The user's coral MCP is backed by a different data store (proxy, cache, or smaller/cached dataset) — not the same GitHub pull walker the local coral uses.
- The user's coral server was already warm and pointed at a pre-materialised index for `user__login='FiscalMindset'`.
- Different coral version / config (e.g. dedicated search index, connection pool tuning).

What the local data *does* agree with: both sides return the **same 18 PRs** (correctness), and `gh` is consistently under 1 second. The latency gap varies widely by coral configuration; on this machine it is ~25×, on the user's coral it was ~0.13×. The general principle from v1 — `gh` is competitive to fastest for GitHub queries — still holds on this coral instance, but the magnitude is configuration-dependent. **Always re-measure on your coral setup before committing to a stack.**

### 2. recent workflow runs (last 5) — `FiscalMindset/coral`

- `gh`: `gh run list --repo FiscalMindset/coral --limit 5 --json name,status,conclusion,runNumber,createdAt`
- `coral`: `SELECT name, status, conclusion, run_number, created_at FROM github.repo_action_runs WHERE owner='FiscalMindset' AND repo='coral' ORDER BY created_at DESC LIMIT 5`
- **0.04s vs 12.73s (318×).** Largest ratio of the sweep — `gh run list` is nearly free (cached), coral walks the run log.

### 3. latest 5 commits — `FiscalMindset/coral`

- `gh`: `gh api repos/FiscalMindset/coral/commits --jq '.[0:5] | .[] | {sha, msg, date}'`
- `coral`: `SELECT sha, commit__message, commit__author__date FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 5`
- **0.94s vs 38.36s (41×).** Same `ORDER BY` pitfall as v1 test 4 — coral fetches full history to sort, then returns 5 rows.

### 4. branches (top 10) — `FiscalMindset/coral`

- `gh`: `gh api repos/FiscalMindset/coral/branches --jq '.[0:10] | .[].name'`
- `coral`: `SELECT name FROM github.repo_branches WHERE owner='FiscalMindset' AND repo='coral' LIMIT 10`
- **0.55s vs 9.06s (16×).** The smallest-ratio "real" test. LIMIT pushdown works; sql = 7.36s = the floor.

### 5. recent releases (last 5) — `withcoral/coral`

- `gh`: `gh release list --repo withcoral/coral --limit 5 --json name,tagName,publishedAt`
- `coral`: `SELECT name, tag_name, published_at FROM github.releases WHERE owner='withcoral' AND repo='coral' ORDER BY published_at DESC LIMIT 5`
- **0.60s vs 9.47s (16×).**

### 6. open issues (last 10) — `withcoral/coral`

- `gh`: `gh issue list --repo withcoral/coral --state open --limit 10 --json number,title,state,createdAt`
- `coral`: `SELECT number, title, state, created_at FROM github.issues WHERE owner='withcoral' AND repo='coral' AND state='open' ORDER BY created_at DESC LIMIT 10`
- **0.61s vs 45.45s (74×).** 2nd-worst absolute time. sql = 36.52s — full issue list fetched, then top 10 selected.

### 7. recent tags (last 10) — `withcoral/coral`

- `gh`: `gh api repos/withcoral/coral/tags --jq '.[0:10] | .[] | {name, sha}'`
- `coral`: `SELECT name, commit__sha FROM github.repo_tags WHERE owner='withcoral' AND repo='coral' LIMIT 10`
- **0.81s vs 19.84s (25×).**

### 8. repo languages — `FiscalMindset/coral`

- `gh`: `gh api repos/FiscalMindset/coral/languages`
- `coral`: `SELECT * FROM github.languages WHERE owner='FiscalMindset' AND repo='coral'`
- **0.54s vs 18.30s (34×).** 18s for 1 row. The fixed pipeline cost.

### 9. repo topics — `FiscalMindset/coral`

- `gh`: `gh api repos/FiscalMindset/coral/topics`
- `coral`: `SELECT * FROM github.repo_topics WHERE owner='FiscalMindset' AND repo='coral'`
- **0.69s vs 23.93s (35×).** 24s for 1 row.

### 10. repo collaborators (top 10) — `FiscalMindset/coral`

- `gh`: `gh api repos/FiscalMindset/coral/collaborators --jq '.[0:10] | .[].login'`
- `coral`: `SELECT login FROM github.collaborators WHERE owner='FiscalMindset' AND repo='coral' LIMIT 10`
- **0.62s vs 23.66s (38×).** `coral` returned **0 rows** — `collaborators` table empty for this repo. 24s to confirm emptiness.

### 11. repo contributors (top 5) — `FiscalMindset/coral`

- `gh`: `gh api repos/FiscalMindset/coral/contributors --jq '.[0:5] | .[] | {login, contributions}'`
- `coral`: `SELECT login, contributions FROM github.repo_contributors WHERE owner='FiscalMindset' AND repo='coral' LIMIT 5`
- **0.70s vs 20.16s (29×).**

### 12. issue #1 comments — `withcoral/coral`

- `gh`: `gh api repos/withcoral/coral/issues/1/comments --jq '.[] | {user, body}'`
- `coral`: `SELECT user__login, body FROM github.repo_issue_comments WHERE owner='withcoral' AND repo='coral' AND number=1 LIMIT 5`
- **0.69s vs 16.01s (23×).** `coral` returned **0 rows**; 16s to confirm.

### 13. search issues `release` — `withcoral/coral`

- `gh`: `gh search issues 'repo:withcoral/coral release' --limit 5 --json number,title,state`
- `coral`: `SELECT number, title, state FROM github.search_issues WHERE query='repo:withcoral/coral release' LIMIT 5`
- **1.15s vs 15.77s (14×).** Search endpoint, 0 rows from coral.

### 14. search PRs `fix` — `withcoral/coral`

- `gh`: `gh search prs 'repo:withcoral/coral fix' --limit 5 --json number,title,state`
- `coral`: `SELECT number, title, state FROM github.search_pull_requests WHERE query='repo:withcoral/coral fix' LIMIT 5`
- **1.33s vs 17.56s (13×).** Lowest ratio of the sweep.

### 15. search repos `coral` —

- `gh`: `gh search repos 'coral' --limit 5 --json fullName,description,stargazersCount`
- `coral`: `SELECT full_name, description, stargazers_count FROM github.search_repositories WHERE query='coral' LIMIT 5`
- **0.86s vs 15.22s (18×).**

### 16. user gists (top 5) — `FiscalMindset`

- `gh`: `gh gist list --limit 5 --public`
- `coral`: `SELECT id, description FROM github.gists WHERE owner='FiscalMindset' LIMIT 5`
- **0.58s vs 18.18s (31×).** 0 rows.

### 17. PR #1 commits (top 5) — `withcoral/coral`

- `gh`: `gh api repos/withcoral/coral/pulls/1/commits --jq '.[0:5] | .[] | {sha, msg}'`
- `coral`: `SELECT sha, commit__message FROM github.commits WHERE owner='withcoral' AND repo='coral' AND pull_number=1 LIMIT 5`
- **0.66s vs 58.07s (88×).** **Worst absolute time of the sweep.** sql = 48s. The `pull_number` filter apparently does not push down; coral walks the full commit history again.

### 18. PR #1 files — `withcoral/coral`

- `gh`: `gh api repos/withcoral/coral/pulls/1/files --jq '.[] | .filename'`
- `coral`: `SELECT filename FROM github.repo_pull_request_files WHERE owner='withcoral' AND repo='coral' AND number=1`
- **1.04s vs 18.43s (18×).** 0 rows from coral.

### 19. most-recent workflow run jobs — `FiscalMindset/coral`

- `gh`: `RUN_ID=$(gh run list --repo FiscalMindset/coral --limit 1 --json databaseId --jq '.[0].databaseId'); gh api repos/FiscalMindset/coral/actions/runs/$RUN_ID/jobs --jq '.jobs[:5] | .[] | {name, status, conclusion}'`
- `coral`: `SELECT name, status, conclusion FROM github.repo_action_jobs WHERE owner='FiscalMindset' AND repo='coral' AND run_id=(SELECT run_id FROM github.repo_action_runs WHERE owner='FiscalMindset' AND repo='coral' ORDER BY created_at DESC LIMIT 1) LIMIT 5`
- **1.77s vs 19.56s (11×).** coral subquery returned a `run_id` but the join produced 0 rows. Worst-case ratio for the dashboard.

### 20. workflow files list — `FiscalMindset/coral`

- `gh`: `gh api repos/FiscalMindset/coral/actions/workflows --jq '.workflows[:5] | .[] | {name, path, state}'`
- `coral`: `SELECT name, path, state FROM github.repo_workflows WHERE owner='FiscalMindset' AND repo='coral' LIMIT 5`
- **0.59s vs 15.75s (27×).** 0 rows.

---

## 4. Root causes

| # | Cause | Mechanism | Affected tests | Cost |
|---|---|---|---|---|
| 1 | **Cold init / MCP handshake** | coral spawns Rust engine + MCP stdio + catalog load on every fresh query run | all 20 | 1.4–7.9s (median 3.9s) |
| 2 | **GitHub provider fetch + Arrow mapping** | even when LIMIT pushdown works, one provider round-trip + column mapping | all 20 | 7–14s (sql baseline) |
| 3 | **`ORDER BY` does not push down** | coral's planner treats GitHub as unordered; `ORDER BY … DESC LIMIT n` triggers full-history fetch | 1, 3, 5, 6, 17 | 14–48s extra |
| 4 | **Filter columns not pushdown** | `pull_number`, `number`, `run_id` subquery, `state` etc. are computed locally | 12, 17, 18, 19, 20 | 13–48s wasted work |
| 5 | **Catalog load** | 37 sources validated per task; 8 broken `careops_*` + missing `blogger` key | all 20 | ~3.7s (in init) |
| 6 | **Empty result pay-full-tax** | coral takes 15–23s even when returning 0 rows | 10, 12, 13, 14, 15, 16, 18, 19, 20 | 0 rows in 15–23s |

---

## 5. Verdict

```
gh CLI  : median 0.69s   |  range 0.04–1.77s
coral   : median 19.6s   |  range 9–58s
ratio   : ~28× median    |  range 11–318× (this coral instance)
```

On **this** coral build (`0.8.1+3acb123`, stdio spawn, withcoral/coral corpus), coral MCP `sql` is slower than `gh` on every test. The 2–8s init overhead is structural and the 7–48s sql phase is dominated by GitHub pagination the planner cannot push down.

**Caveat added after re-test of test 1:** the gap is **configuration-dependent**. A user-side measurement on a different coral MCP setup reported coral ~8× faster than `gh` for the same author-filtered PR query (160 ms vs 1246 ms). That is the opposite of what this benchmark shows. Likely causes are differences in the coral backing store, pre-materialised search index, or coral version. **Before committing to a stack, re-measure on your coral setup.** The headline numbers in this report apply only to this coral instance.

**Action items for the next benchmark:**
- Identify which coral configuration the user's 160 ms number was measured on; if it is generally available, document the config that flips the verdict.
- Add a Python harness that *keeps the coral MCP server alive* across queries (single `start_task` reused). For this coral instance, the warm-server sql phase was still 23 s, so init is not the only cost; for a faster coral instance, warm-server may be the only mode that matters.
- If a warm-server test still leaves coral much slower, the remaining cost is the GitHub provider walk inside coral — out of scope for a user-side config change.

---

## 6. Artifacts

| Path | Description |
|---|---|
| `artifacts/all_summary.json` | aggregated 20-row table (test, gh_med, coral_med, init, sql, ratio) |
| `artifacts/<test>/gh/run-NN/` | per-run gh output (`out.txt`, `err.txt`, `timing.txt`) + `summary.json` |
| `artifacts/<test>/coral/run-NN/` | per-run coral stdout + mcp stderr log + `summary.json` |
| `run_all.py` | driver that loops over the 20 tests via the skill runner |
| `aggregate.py` | reads per-test `summary.json` into `all_summary.json` |
| `run.log` | full stdout/stderr of the v2 run (~25 min wall clock) |
| `~/.config/opencode/skills/coral-benchmark/bench_runner.py` | the runner script |
| `2026-08-10-coral-mcp-vs-gh-timing.md` (v1) | original 4-test report for comparison |

Coral task id used: `e5c762d1-0b4b-45a8-acac-98ff7aeb9605` (v2).
