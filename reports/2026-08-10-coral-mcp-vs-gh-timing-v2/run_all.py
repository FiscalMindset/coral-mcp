import subprocess, sys, os

TESTS = [
    {
        "name": "t01_open_prs_withcoral",
        "label": "withcoral/coral open PRs (top 20)",
        "gh_cmd": "gh pr list --repo withcoral/coral --state open --limit 20 --json number,title,state,createdAt",
        "query": "SELECT number, title, state, created_at FROM github.pulls WHERE owner='withcoral' AND repo='coral' AND state='open' ORDER BY created_at DESC LIMIT 20",
    },
    {
        "name": "t02_recent_runs_fm",
        "label": "FiscalMindset/coral recent workflow runs (last 5)",
        "gh_cmd": "gh run list --repo FiscalMindset/coral --limit 5 --json name,status,conclusion,runNumber,createdAt",
        "query": "SELECT name, status, conclusion, run_number, created_at FROM github.repo_action_runs WHERE owner='FiscalMindset' AND repo='coral' ORDER BY created_at DESC LIMIT 5",
    },
    {
        "name": "t03_commits_fm",
        "label": "FiscalMindset/coral latest 5 commits",
        "gh_cmd": "gh api repos/FiscalMindset/coral/commits --jq '.[0:5] | .[] | {sha: .sha[0:7], msg: (.commit.message | split(\"\\n\")[0]), date: .commit.author.date}'",
        "query": "SELECT sha, commit__message, commit__author__date FROM github.commits WHERE owner='FiscalMindset' AND repo='coral' ORDER BY commit__author__date DESC LIMIT 5",
    },
    {
        "name": "t04_branches_fm",
        "label": "FiscalMindset/coral branches (top 10)",
        "gh_cmd": "gh api repos/FiscalMindset/coral/branches --jq '.[0:10] | .[].name'",
        "query": "SELECT name FROM github.repo_branches WHERE owner='FiscalMindset' AND repo='coral' LIMIT 10",
    },
    {
        "name": "t05_releases_withcoral",
        "label": "withcoral/coral recent releases (last 5)",
        "gh_cmd": "gh release list --repo withcoral/coral --limit 5 --json name,tagName,publishedAt",
        "query": "SELECT name, tag_name, published_at FROM github.releases WHERE owner='withcoral' AND repo='coral' ORDER BY published_at DESC LIMIT 5",
    },
    {
        "name": "t06_open_issues_withcoral",
        "label": "withcoral/coral open issues (last 10)",
        "gh_cmd": "gh issue list --repo withcoral/coral --state open --limit 10 --json number,title,state,createdAt",
        "query": "SELECT number, title, state, created_at FROM github.issues WHERE owner='withcoral' AND repo='coral' AND state='open' ORDER BY created_at DESC LIMIT 10",
    },
    {
        "name": "t07_tags_withcoral",
        "label": "withcoral/coral recent tags (last 10)",
        "gh_cmd": "gh api repos/withcoral/coral/tags --jq '.[0:10] | .[] | {name, sha: .commit.sha[0:7]}'",
        "query": "SELECT name, commit__sha FROM github.repo_tags WHERE owner='withcoral' AND repo='coral' LIMIT 10",
    },
    {
        "name": "t08_languages_fm",
        "label": "FiscalMindset/coral languages",
        "gh_cmd": "gh api repos/FiscalMindset/coral/languages",
        "query": "SELECT * FROM github.languages WHERE owner='FiscalMindset' AND repo='coral'",
    },
    {
        "name": "t09_topics_fm",
        "label": "FiscalMindset/coral topics",
        "gh_cmd": "gh api repos/FiscalMindset/coral/topics",
        "query": "SELECT * FROM github.repo_topics WHERE owner='FiscalMindset' AND repo='coral'",
    },
    {
        "name": "t10_collaborators_fm",
        "label": "FiscalMindset/coral collaborators (top 10)",
        "gh_cmd": "gh api repos/FiscalMindset/coral/collaborators --jq '.[0:10] | .[] | .login'",
        "query": "SELECT login FROM github.collaborators WHERE owner='FiscalMindset' AND repo='coral' LIMIT 10",
    },
    {
        "name": "t11_contributors_fm",
        "label": "FiscalMindset/coral contributors (top 5)",
        "gh_cmd": "gh api repos/FiscalMindset/coral/contributors --jq '.[0:5] | .[] | {login, contributions}'",
        "query": "SELECT login, contributions FROM github.repo_contributors WHERE owner='FiscalMindset' AND repo='coral' LIMIT 5",
    },
    {
        "name": "t12_issue_comments_withcoral",
        "label": "withcoral/coral issue #1 comments",
        "gh_cmd": "gh api repos/withcoral/coral/issues/1/comments --jq '.[] | {user: .user.login, body: (.body | .[0:80])}'",
        "query": "SELECT user__login, body FROM github.repo_issue_comments WHERE owner='withcoral' AND repo='coral' AND number=1 LIMIT 5",
    },
    {
        "name": "t13_search_issues_withcoral",
        "label": "Search issues: 'release' (withcoral/coral)",
        "gh_cmd": "gh search issues 'repo:withcoral/coral release' --limit 5 --json number,title,state",
        "query": "SELECT number, title, state FROM github.search_issues WHERE query='repo:withcoral/coral release' LIMIT 5",
    },
    {
        "name": "t14_search_prs_withcoral",
        "label": "Search PRs: 'fix' (withcoral/coral)",
        "gh_cmd": "gh search prs 'repo:withcoral/coral fix' --limit 5 --json number,title,state",
        "query": "SELECT number, title, state FROM github.search_pull_requests WHERE query='repo:withcoral/coral fix' LIMIT 5",
    },
    {
        "name": "t15_search_repos_coral",
        "label": "Search repos: 'coral'",
        "gh_cmd": "gh search repos 'coral' --limit 5 --json fullName,description,stargazersCount",
        "query": "SELECT full_name, description, stargazers_count FROM github.search_repositories WHERE query='coral' LIMIT 5",
    },
    {
        "name": "t16_gists_fm",
        "label": "FiscalMindset public gists (top 5)",
        "gh_cmd": "gh gist list --limit 5 --public",
        "query": "SELECT id, description FROM github.gists WHERE owner='FiscalMindset' LIMIT 5",
    },
    {
        "name": "t17_pr_commits_withcoral",
        "label": "withcoral/coral PR #1 commits (top 5)",
        "gh_cmd": "gh api repos/withcoral/coral/pulls/1/commits --jq '.[0:5] | .[] | {sha: .sha[0:7], msg: (.commit.message | split(\"\\n\")[0])}'",
        "query": "SELECT sha, commit__message FROM github.commits WHERE owner='withcoral' AND repo='coral' AND pull_number=1 LIMIT 5",
    },
    {
        "name": "t18_pr_files_withcoral",
        "label": "withcoral/coral PR #1 files",
        "gh_cmd": "gh api repos/withcoral/coral/pulls/1/files --jq '.[] | .filename'",
        "query": "SELECT filename FROM github.repo_pull_request_files WHERE owner='withcoral' AND repo='coral' AND number=1",
    },
    {
        "name": "t19_workflow_jobs_fm",
        "label": "FiscalMindset/coral most-recent workflow run jobs",
        "gh_cmd": "RUN_ID=$(gh run list --repo FiscalMindset/coral --limit 1 --json databaseId --jq '.[0].databaseId'); gh api repos/FiscalMindset/coral/actions/runs/$RUN_ID/jobs --jq '.jobs[:5] | .[] | {name, status, conclusion}'",
        "query": "SELECT name, status, conclusion FROM github.repo_action_jobs WHERE owner='FiscalMindset' AND repo='coral' AND run_id=(SELECT run_id FROM github.repo_action_runs WHERE owner='FiscalMindset' AND repo='coral' ORDER BY created_at DESC LIMIT 1) LIMIT 5",
    },
    {
        "name": "t20_actions_workflows_fm",
        "label": "FiscalMindset/coral workflow files",
        "gh_cmd": "gh api repos/FiscalMindset/coral/actions/workflows --jq '.workflows[:5] | .[] | {name, path, state}'",
        "query": "SELECT name, path, state FROM github.repo_workflows WHERE owner='FiscalMindset' AND repo='coral' LIMIT 5",
    },
]

RUNNER = os.path.expanduser("~/.config/opencode/skills/coral-benchmark/bench_runner.py")
OUTDIR = "/Users/viclkykumar/code/coral-mcp-benchmark/reports/2026-08-10-coral-mcp-vs-gh-timing-v2/artifacts"
TASK_ID = "e5c762d1-0b4b-45a8-acac-98ff7aeb9605"
INTENT = "v2 benchmark: 20 GitHub commands"

failures = []
for t in TESTS:
    cmd = ["python3", RUNNER, "--tools", "gh", "coral",
           "--test", t["name"], "--gh-cmd", t["gh_cmd"], "--query", t["query"],
           "--task-id", TASK_ID, "--intent", INTENT,
           "--runs", "3", "--warmup", "1", "--outdir", OUTDIR]
    print("\n=== %s (%s) ===" % (t["name"], t["label"]), flush=True)
    rc = subprocess.call(cmd)
    if rc != 0:
        failures.append(t["name"])
        print("  !! FAILED rc=%d" % rc, flush=True)

if failures:
    print("\nFAILURES: %s" % failures)
    sys.exit(1)
print("\nALL 20 DONE")