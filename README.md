# coral-mcp-benchmark

Coral MCP benchmark work — runner, reports, and the opencode sessions that drove it.

## Folder layout

```
.
├── bench_runner.py            # coral-benchmark skill runner
├── reports/                   # generated benchmark reports (.md + .html)
└── *.json                     # opencode session exports (opencode export <sessionID>)
```

## opencode sessions (raw `opencode export` JSON)

| File | Title | Session | Msgs (U/A) | When |
|---|---|---|---|---|
| `2026-08-10-parallel-github-pr-query-comparison.json` | Parallel GitHub PR query comparison (**← where the coral-vs-gh report was built**) | `ses_01543b459ffehEcRXd9rfc3Y2V` | 16 | 2026-08-10 08:31 UTC |
| `2026-08-09-compare-coral-mcp-vs-direct-api-timing.json` | Compare Coral MCP vs Direct API timing | `ses_019462766ffe9Mc3vLu8tWihc6` | 8 (1/7) | 2026-08-09 13:32 UTC |
| `2026-08-09-parallel-coral-mcp-vs-direct-api-timing.json` | Parallel Coral MCP vs Direct API timing | `ses_01944c26dffeqTfRWkeu5kdzr4` | 6 (1/5) | 2026-08-09 13:34 UTC |
| `2026-08-09-coral-repo-promotion-fiscalmindset-pr-review.json` | Coral-repo promotion with fiscalmindset PR review | `ses_0196346aeffeSjabzDJ4nAcGL7` | 86 (31/55) | 2026-08-09 → 2026-08-12 |
| `2026-08-10-research-commercial-scraping-solutions-and-benchmarks.json` | Research commercial scraping solutions and benchmarks | `ses_014fa6a09ffeNV4xI76U0fNIfD` | 11 (1/10) | 2026-08-10 09:33 UTC |

JSON shape: `{ info: { id, title, time, ... }, messages: [ { info: { role, ... }, parts: [ ... ] } ] }`. Each `part` has a `type` (`text`, `tool`, `reasoning`, `step-start`, `step-finish`) and a payload.

## Re-export / import a session

```bash
# export
opencode export <sessionID> > <slug>.json

# import back into opencode
opencode import <slug>.json

# list / delete
opencode session list
opencode session delete <sessionID>
```

Use `--sanitize` to redact secrets if you plan to share a JSON with someone like Andrea:

```bash
opencode export --sanitize <sessionID> > <slug>.json
```

The source SQLite DB lives at `~/.local/share/opencode/opencode.db` (tables: `session`, `message`, `part`).

## Making old sessions show in `/session` for this folder

opencode's TUI `/session` lists sessions with two filters:
1. `directory == current working directory` (server-side, exact match)
2. `parent_id IS NULL` — only **root** sessions, not subagents spawned by `@general subagent`

The 5 exported sessions were originally started from `/Users/viclkykumar` and four of them are subagents (`parent_id != NULL`). Two SQL updates were applied (after backing up the DB to `~/.local/share/opencode/opencode.db.bak.<timestamp>`):

```sql
UPDATE session SET directory='/Users/viclkykumar/code/coral-mcp-benchmark'
WHERE id IN ('ses_01543b459ffehEcRXd9rfc3Y2V',
             'ses_019462766ffe9Mc3vLu8tWihc6',
             'ses_01944c26dffeqTfRWkeu5kdzr4',
             'ses_014fa6a09ffeNV4xI76U0fNIfD',
             'ses_0196346aeffeSjabzDJ4nAcGL7');

UPDATE session SET parent_id=NULL
WHERE id IN (...same IDs...);
```

After both updates, the 5 sessions show in `/session` when opencode is started from this folder.

To undo:

```sql
UPDATE session SET directory='/Users/viclkykumar', parent_id=<original_parent_id>
WHERE id IN (...);
```
