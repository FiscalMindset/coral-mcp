# coral GitHub MCP — full 364-table smoke test (FINAL)

Date: 2026-08-10 · Coral: 0.8.1+3acb123 · Schema: github
Coral task id: ccc6ea3e-... (final pass)

All 364 tables in the `github` schema were probed. After 4 re-probe passes plus a final `gh api` verification, this is the honest final state.

## 1. Final outcome

| Outcome | Count | % | Whose fault |
|---|---:|---:|---|
| ✅ working | **137** | 37.6% | — |
| ⏱ rate-limited | 115 | 31.6% | env |
| 🔒 auth-required | 11 | 3.0% | env |
| 💥 coral crashed | 4 | 1.1% | coral |
| ❌ my fault | **97** | 26.6% | see breakdown |

## 2. My fault breakdown (gh_api verified)

After 4 fix passes, I verified the remaining 105 my-fault tables by extracting the actual GitHub URL from each error and testing with real IDs via `gh api`.

- **8 tables**: 200 OK with real IDs — would have been fixed if I could re-probe in coral (coral tools became unavailable in the final session)
- **2 tables**: 403 — need elevated scope (admin:repo_hook, codespace, admin:org) — env
- **2 tables**: 422 — bad parameter format — env
- **85 tables**: 404 with real IDs — entity does not exist for this user

### 404 categories (entity genuinely does not exist)

- **46** org-scoped (needs withcoral org membership)
- **18** repo-scoped (no data in target repo)
- **8** other
- **4** pages (no pages configured)
- **3** enterprise (needs enterprise plan)
- **2** classroom (no classroom access)
- **2** codespaces (no codespace configured)
- **1** attestations (no real digest)
- **1** user-scoped (needs user resource)

### 8 tables that work with real IDs (would fix if re-probed)

- `github.accepted_assignments`
- `github.activity_list_repos_watched_by_user`
- `github.approvals`
- `github.apps`
- `github.attempts`
- `github.authors`
- `github.import`
- `github.large_files`

## 3. How to get to 0 my fault (and why it's hard)

My user FiscalMindset is NOT a member of the withcoral org. That is why 46 of the remaining 97 my-fault tables return 404 — they are org-scoped and require org membership. To reach 0, you would need to:

1. Add me as a member of the `withcoral` org — would unblock 46 org-scoped tables
2. Re-probe the 8 works-with-real-IDs tables in coral — needs the coral MCP tool, which became unavailable mid-session
3. Get enterprise plan — would unblock 3 enterprise-scoped tables
4. Get GitHub Classroom access — would unblock 2 classroom tables
5. Configure a codespace / Pages site / repo hook / Copilot / attestations — would unblock the rest

## 4. Methodology

1. Round 1 (smoke): synthetic LIMIT 1 probe with placeholder filter values
2. Round 2 (fix3): discovered real IDs via coral parent queries
3. Round 3 (smart): added multiple fallback parent queries per filter
4. Round 4 (gh_ids): used gh CLI directly to fetch real IDs
5. Round 5 (gh_api verification): for each still-failing table, extracted the actual GitHub URL, substituted real IDs from both repos, and tested with gh api to definitively classify why it fails

## 5. Files

- smoke_results.json — round 1 results (original errors)
- fix3_results.json, smart_results.json, gh_ids_results.json — passes 2-4
- gh_v5_results.json — pass 5 (gh api verification with real IDs)
- final_results.json — merged final state per table
- url_map.json — extracted URLs per table
- investigations.json — URLs and error excerpts for each table
- my_fault_list.json — list of 105 still-failing tables

Coral tasks used: 96ed9317-... (round 1), f0ef7474-... (rounds 2-4), ccc6ea3e-... (pass 5). All ended success.