# coral GitHub MCP — full catalog report

**Date:** 2026-08-10  ·  **Coral:** `0.8.1+3acb123`  ·  **Schema:** `github`
**Coral task id:** `24a2d2f3-d459-4bf0-8804-879ff561a25a`

A complete inventory of every queryable surface exposed by the `github` schema of the coral MCP server: **364 tables** + **7 search functions**.

## Summary

- **364 tables** (across 29 categories)
- **7 search functions**: `search_code`, `search_commits`, `search_issues`, `search_labels`, `search_repositories`, `search_topics`, `search_users`
- **308 tables have required filters** (most need `owner` + `repo`, or an entity id like `run_id`, `job_id`, `number`)
- Total columns across all tables: **0**

| Category | Tables |
|---|---:|
| Pull requests | 7 |
| Issues | 13 |
| Commits / branches / git | 21 |
| Tags / releases / deployments | 16 |
| Repository metadata | 60 |
| Actions / workflows | 26 |
| Users / orgs / teams / members | 53 |
| Gists | 7 |
| Comments / reactions / events / timeline / threads | 8 |
| Security: alerts, scanning, advisories, dependabot | 5 |
| Apps / installations / hooks / oauth | 11 |
| Codespaces / devcontainers | 3 |
| Marketplace / billing / plans / seats | 8 |
| Packages / containers | 2 |
| Notifications | 1 |
| Pages (GitHub Pages) | 1 |
| Insights / metrics / activity / clones / referrers | 4 |
| Copilot | 1 |
| Projects v2 | 1 |
| Enterprise / admin | 1 |
| Checks / status | 1 |
| Interactions / limits / blocks | 2 |
| Rule suites / rulesets / branch protection | 7 |
| Forks / invitations / subscriptions | 2 |
| Custom / variants / codeql variants | 2 |
| Other (admin / class / meta / versions / etc.) | 101 |
| **TOTAL** | **364** |

## Search functions (table functions)

These are invoked via `coral_search_*` tool, not as plain SQL tables. Each returns a result-set you can SELECT from.

| Function | Description | Use case |
|---|---|---|
| `search_code` | Search GitHub code | `SELECT * FROM search_code('query string')` |
| `search_commits` | Search GitHub commits | `SELECT * FROM search_commits('query string')` |
| `search_issues` | Search GitHub issues and pull requests | `SELECT * FROM search_issues('query string')` |
| `search_labels` | Search GitHub labels in a repository | `SELECT * FROM search_labels('query string')` |
| `search_repositories` | Search GitHub repositories | `SELECT * FROM search_repositories('query string')` |
| `search_topics` | Search GitHub topics | `SELECT * FROM search_topics('query string')` |
| `search_users` | Search GitHub users | `SELECT * FROM search_users('query string')` |

## Per-category tables

### Pull requests (7 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.pulls` | owner, repo, owner, repo | gh pr list / gh pr view |
| `github.pulls_list_review_comments` | owner, repo, pull_number, owner, pull_number, repo | gh api repos/o/r/pulls/{n}/comments |
| `github.repo_pull_comments` | owner, repo, owner, repo | — |
| `github.repo_pull_review_comments` | owner, repo, pull_number, review_id, owner, pull_number, repo, review_id | — |
| `github.requested_reviewers` | owner, repo, pull_number, owner, pull_number, repo | — |
| `github.required_pull_request_reviews` | owner, repo, branch, branch, owner, repo | — |
| `github.reviews` | owner, repo, pull_number, owner, pull_number, repo | gh pr view --json reviews |

### Issues (13 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.issue_field_values` | owner, repo, issue_number, issue_number, owner, repo | — |
| `github.issue_fields` | org, org | — |
| `github.issue_types` | org, org | — |
| `github.issues` | — | gh issue list / gh issue view |
| `github.issues_list_comments` | owner, repo, issue_number, issue_number, owner, repo | gh api repos/o/r/issues/{n}/comments |
| `github.issues_list_events` | owner, repo, issue_number, issue_number, owner, repo | gh api repos/o/r/issues/{n}/events |
| `github.labels` | org, runner_id, org, runner_id | — |
| `github.milestones` | owner, repo, owner, repo | — |
| `github.repo_issue_comments` | owner, repo, owner, repo | — |
| `github.repo_issue_events` | owner, repo, owner, repo | — |
| `github.repo_labels` | owner, repo, owner, repo | — |
| `github.sub_issues` | owner, repo, issue_number, issue_number, owner, repo | — |
| `github.user_issues` | — | — |

### Commits / branches / git (21 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.blobs` | owner, repo, file_sha, file_sha, owner, repo | — |
| `github.branches_where_head` | owner, repo, commit_sha, commit_sha, owner, repo | — |
| `github.commit_activity` | owner, repo, owner, repo | — |
| `github.commits` | owner, repo, owner, repo | gh api repos/o/r/commits |
| `github.deployment_branch_policies` | owner, repo, environment_name, environment_name, owner, repo | — |
| `github.gist_commits` | gist_id, gist_id | — |
| `github.matching_refs` | owner, repo, ref, owner, ref, repo | — |
| `github.ref` | owner, repo, ref, owner, ref, repo | — |
| `github.referrers` | owner, repo, owner, repo | — |
| `github.repo_branch_protection_restriction_apps` | owner, repo, branch, branch, owner, repo | — |
| `github.repo_branch_protection_restriction_teams` | owner, repo, branch, branch, owner, repo | — |
| `github.repo_branch_protection_restriction_users` | owner, repo, branch, branch, owner, repo | — |
| `github.repo_branches` | owner, repo, owner, repo | gh api repos/o/r/branches |
| `github.repo_commit_check_suites` | owner, repo, ref, owner, ref, repo | — |
| `github.repo_commit_statuses` | owner, repo, ref, owner, ref, repo | — |
| `github.repo_compare` | owner, repo, basehead, basehead, owner, repo | — |
| `github.repo_dependency_graph_compare` | owner, repo, basehead, basehead, owner, repo | — |
| `github.repo_git_commits` | owner, repo, commit_sha, commit_sha, owner, repo | — |
| `github.repo_git_tags` | owner, repo, tag_sha, owner, repo, tag_sha | — |
| `github.repo_rule_branches` | owner, repo, branch, branch, owner, repo | — |
| `github.trees` | owner, repo, tree_sha, owner, repo, tree_sha | — |

### Tags / releases / deployments (16 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.deployment_protection_rules` | environment_name, repo, owner, environment_name, owner, repo | — |
| `github.deployment_records` | org, subject_digest, org, subject_digest | — |
| `github.org_setting_immutable_release_repositories` | org, org | — |
| `github.org_setting_immutable_releases` | org, org | — |
| `github.pending_deployments` | owner, repo, run_id, owner, repo, run_id | — |
| `github.releases` | owner, repo, owner, repo | gh release list / gh release view |
| `github.repo_deployment_statuses` | owner, repo, deployment_id, deployment_id, owner, repo | — |
| `github.repo_deployments` | owner, repo, owner, repo | gh api repos/o/r/deployments |
| `github.repo_environment_deployment_protection_rule_apps` | environment_name, repo, owner, environment_name, owner, repo | — |
| `github.repo_immutable_releases` | owner, repo, owner, repo | — |
| `github.repo_page_deployments` | owner, repo, pages_deployment_id, owner, pages_deployment_id, repo | — |
| `github.repo_release_assets` | owner, repo, asset_id, asset_id, owner, repo | — |
| `github.repo_release_latest` | owner, repo, owner, repo | — |
| `github.repo_release_tags` | owner, repo, tag, owner, repo, tag | — |
| `github.repo_tags` | owner, repo, owner, repo | gh api repos/o/r/tags |
| `github.repos_list_release_assets` | owner, repo, release_id, owner, release_id, repo | — |

### Repository metadata (60 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.activity_list_repos_starred_by_user` | username, username | — |
| `github.activity_list_repos_watched_by_user` | username, username | — |
| `github.enterprise_code_security_configuration_repositories` | enterprise, configuration_id, configuration_id, enterprise | — |
| `github.enterprise_copilot_metric_report_enterprise_28_day_latest` | enterprise, enterprise | — |
| `github.fork_pr_workflows_private_repos` | org, org | — |
| `github.installation_repositories` | — | — |
| `github.languages` | owner, repo, owner, repo | gh api repos/o/r/languages |
| `github.license` | owner, repo, owner, repo | — |
| `github.licenses` | — | — |
| `github.org_action_permission_repositories` | org, org | — |
| `github.org_action_permission_self_hosted_runner_repositories` | org, org | — |
| `github.org_attestation_repositories` | org, org | — |
| `github.org_copilot_coding_agent_permission_repositories` | org, org | — |
| `github.org_copilot_metric_report_organization_28_day_latest` | org, org | — |
| `github.org_repos` | org, org | — |
| `github.private_vulnerability_reporting` | owner, repo, owner, repo | — |
| `github.readme` | owner, repo, owner, repo | — |
| `github.repo` | enterprise, enterprise | — |
| `github.repo_action_artifacts` | owner, repo, owner, repo | gh api repos/o/r/actions/runs/{id}/artifacts |
| `github.repo_action_cache_usage` | owner, repo, owner, repo | — |
| `github.repo_action_jobs` | owner, repo, job_id, job_id, owner, repo | gh api repos/o/r/actions/runs/{id}/jobs |
| `github.repo_action_oidc_customization_sub` | owner, repo, owner, repo | — |
| `github.repo_action_permissions` | owner, repo, owner, repo | — |
| `github.repo_action_run_artifacts` | owner, repo, run_id, owner, repo, run_id | — |
| `github.repo_action_run_timing` | owner, repo, run_id, owner, repo, run_id | — |
| `github.repo_action_runs` | owner, repo, owner, repo | gh run list / gh api repos/o/r/actions/runs |
| `github.repo_action_secrets` | owner, repo, owner, repo | — |
| `github.repo_action_variables` | owner, repo, owner, repo | — |
| `github.repo_action_workflow_runs` | owner, repo, workflow_id, owner, repo, workflow_id | — |
| `github.repo_action_workflow_timing` | owner, repo, workflow_id, owner, repo, workflow_id | — |
| `github.repo_check_runs` | owner, repo, check_run_id, check_run_id, owner, repo | gh api repos/o/r/commits/{sha}/check-runs |
| `github.repo_check_suites` | owner, repo, check_suite_id, check_suite_id, owner, repo | — |
| `github.repo_code_scanning_alerts` | owner, repo, owner, repo | — |
| `github.repo_code_scanning_codeql_variant_analyse_repos` | owner, repo, codeql_variant_analysis_id, repo_owner, repo_name, codeql_variant_analysis_id, owner, repo, repo_name, repo_owner | — |
| `github.repo_codespace_machines` | owner, repo, owner, repo | — |
| `github.repo_codespace_secrets` | owner, repo, owner, repo | — |
| `github.repo_contributors` | owner, repo, owner, repo | gh api repos/o/r/contributors |
| `github.repo_dependabot_alerts` | owner, repo, owner, repo | — |
| `github.repo_dependabot_secrets` | owner, repo, owner, repo | — |
| `github.repo_environment_secret_public_key` | owner, repo, environment_name, environment_name, owner, repo | — |
| `github.repo_environment_secrets` | owner, repo, environment_name, environment_name, owner, repo | — |
| `github.repo_environment_variables` | owner, repo, environment_name, environment_name, owner, repo | — |
| `github.repo_forks` | owner, repo, owner, repo | — |
| `github.repo_hooks` | owner, repo, owner, repo | — |
| `github.repo_invitations` | owner, repo, owner, repo | — |
| `github.repo_keys` | owner, repo, owner, repo | — |
| `github.repo_page_build_latest` | owner, repo, owner, repo | — |
| `github.repo_property_values` | owner, repo, owner, repo | — |
| `github.repo_secret_scanning_alerts` | owner, repo, owner, repo | — |
| `github.repo_stat_contributors` | owner, repo, owner, repo | — |
| `github.repo_subscription` | owner, repo, owner, repo | — |
| `github.repo_topics` | owner, repo, owner, repo | gh api repos/o/r/topics |
| `github.repos` | team_id, owner, repo, owner, repo, team_id | gh search repos / gh api /search/repositories |
| `github.repos_get` | owner, repo, owner, repo | gh repo view |
| `github.repositories` | — | — |
| `github.repository_access` | org, org | — |
| `github.repository_invitations` | — | — |
| `github.usage_by_repository` | org, org | — |
| `github.user_installation_repositories` | installation_id, installation_id | — |
| `github.user_repos` | — | — |

### Actions / workflows (26 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.artifact_and_log_retention` | org, org | — |
| `github.interaction_limits` | org, org | — |
| `github.org_action_cache_usage` | org, org | — |
| `github.org_action_hosted_runner_image_custom_versions` | image_definition_id, org, image_definition_id, org | — |
| `github.org_action_hosted_runners` | org, org | — |
| `github.org_action_oidc_customization_sub` | org, org | — |
| `github.org_action_permissions` | org, org | — |
| `github.org_action_runner_group_hosted_runners` | org, runner_group_id, org, runner_group_id | — |
| `github.org_action_runner_group_runners` | org, runner_group_id, org, runner_group_id | — |
| `github.org_action_secret_public_key` | org, org | — |
| `github.org_action_secrets` | org, org | — |
| `github.org_action_variables` | org, org | — |
| `github.org_codespace_secrets` | org, org | — |
| `github.org_dependabot_secret_public_key` | org, org | — |
| `github.org_dependabot_secrets` | org, org | — |
| `github.org_secret_scanning_alerts` | org, org | — |
| `github.organization_secrets` | owner, repo, owner, repo | — |
| `github.organization_variables` | owner, repo, owner, repo | — |
| `github.runner_groups` | org, org | — |
| `github.runners` | org, org | — |
| `github.self_hosted_runners` | org, org | — |
| `github.user_codespace_secret_public_key` | — | — |
| `github.user_codespace_secrets` | — | — |
| `github.user_interaction_limits` | — | — |
| `github.workflow` | org, org | — |
| `github.workflows` | owner, repo, owner, repo | gh api repos/o/r/actions/workflows |

### Users / orgs / teams / members (53 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.enterprise_team_memberships` | enterprise, enterprise-team, enterprise, enterprise-team | — |
| `github.enterprise_teams` | enterprise, enterprise | — |
| `github.members` | org, org | — |
| `github.memberships` | team_id, username, team_id, username | — |
| `github.org_attestations` | org, subject_digest, org, subject_digest | — |
| `github.org_blocks` | org, org | — |
| `github.org_code_scanning_alerts` | org, org | — |
| `github.org_copilot_coding_agent_permissions` | org, org | — |
| `github.org_hooks` | org, org | — |
| `github.org_insight_summary_stat_users` | org, user_id, min_timestamp, min_timestamp, org, user_id | — |
| `github.org_insight_summary_stats` | org, min_timestamp, min_timestamp, org | — |
| `github.org_insight_time_stat_users` | org, user_id, min_timestamp, timestamp_increment, min_timestamp, org, timestamp_increment, user_id | — |
| `github.org_insight_time_stats` | org, min_timestamp, timestamp_increment, min_timestamp, org, timestamp_increment | — |
| `github.org_insights_summary_stat` | org, min_timestamp, actor_type, actor_id, actor_id, actor_type, min_timestamp, org | — |
| `github.org_insights_time_stat` | org, actor_type, actor_id, min_timestamp, timestamp_increment, actor_id, actor_type, min_timestamp, org, timestamp_increment | — |
| `github.org_installations` | org, org | — |
| `github.org_memberships` | org, username, org, username | — |
| `github.org_migrations` | org, org | — |
| `github.org_organization_role_teams` | org, role_id, org, role_id | — |
| `github.org_organization_role_users` | org, role_id, org, role_id | — |
| `github.org_private_registry_public_key` | org, org | — |
| `github.org_property_values` | org, org | — |
| `github.org_team_memberships` | org, team_slug, username, org, team_slug, username | — |
| `github.organizations` | — | — |
| `github.orgs` | org, org | gh api orgs/{o} |
| `github.orgs_list_for_user` | username, username | — |
| `github.outside_collaborators` | org, org | — |
| `github.public_members` | org, org | — |
| `github.team` | team_id, team_id | — |
| `github.teams` | org, org | gh api orgs/{o}/teams |
| `github.user_blocks` | — | — |
| `github.user_codespace_machines` | codespace_name, codespace_name | — |
| `github.user_codespaces` | — | — |
| `github.user_docker_conflicts` | — | — |
| `github.user_event_orgs` | username, org, org, username | — |
| `github.user_event_public` | username, username | — |
| `github.user_followers` | — | — |
| `github.user_following` | — | — |
| `github.user_gpg_keys` | — | — |
| `github.user_installations` | — | — |
| `github.user_keys` | — | — |
| `github.user_membership_orgs` | — | — |
| `github.user_migrations` | — | — |
| `github.user_orgs` | — | — |
| `github.user_packages` | package_type, package_name, package_name, package_type | — |
| `github.user_received_event_public` | username, username | — |
| `github.user_setting_billing_usage` | username, username | — |
| `github.user_social_accounts` | — | — |
| `github.user_ssh_signing_keys` | — | — |
| `github.user_starred` | — | — |
| `github.user_stats` | org, user_id, min_timestamp, min_timestamp, org, user_id | — |
| `github.user_subscriptions` | — | — |
| `github.user_teams` | — | — |

### Gists (7 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.gist` | gist_id, sha, gist_id, sha | — |
| `github.gist_comments` | gist_id, gist_id | — |
| `github.gist_forks` | gist_id, gist_id | — |
| `github.gist_public` | — | — |
| `github.gist_starred` | — | — |
| `github.gists` | — | gh gist list / gh api gists |
| `github.private_registries` | org, org | — |

### Comments / reactions / events / timeline / threads (8 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.comments` | owner, repo, owner, repo | — |
| `github.events` | — | — |
| `github.notification_thread_subscription` | thread_id, thread_id | — |
| `github.reactions` | owner, repo, comment_id, comment_id, owner, repo | — |
| `github.received_events` | username, username | — |
| `github.subscribers` | owner, repo, owner, repo | — |
| `github.threads` | thread_id, thread_id | — |
| `github.timeline` | owner, repo, issue_number, issue_number, owner, repo | — |

### Security: alerts, scanning, advisories, dependabot (5 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.advisories` | — | — |
| `github.alerts` | org, org | — |
| `github.code_security_configuration` | owner, repo, owner, repo | — |
| `github.sarifs` | owner, repo, sarif_id, owner, repo, sarif_id | — |
| `github.security_advisories` | org, org | — |

### Apps / installations / hooks / oauth (11 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.app` | — | — |
| `github.app_hook_config` | — | — |
| `github.app_hook_deliveries` | — | — |
| `github.app_installations` | — | — |
| `github.approvals` | owner, repo, run_id, owner, repo, run_id | — |
| `github.apps` | app_slug, app_slug | — |
| `github.fork_pr_contributor_approval` | org, org | — |
| `github.installation` | org, org | — |
| `github.installation_requests` | — | — |
| `github.personal_access_token_requests` | org, org | — |
| `github.personal_access_tokens` | org, org | — |

### Codespaces / devcontainers (3 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.codespaces` | org, org | — |
| `github.devcontainers` | owner, repo, owner, repo | — |
| `github.machine_sizes` | org, org | — |

### Marketplace / billing / plans / seats (8 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.billing` | org, org | — |
| `github.marketplace_listing_accounts` | account_id, account_id | — |
| `github.marketplace_listing_plans` | — | — |
| `github.marketplace_listing_stubbed_plans` | — | — |
| `github.marketplace_purchases` | — | — |
| `github.organization_setting_billing_usage` | org, org | — |
| `github.seats` | org, org | — |
| `github.usage` | org, org | — |

### Packages / containers (2 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.packages` | package_type, org, org, package_type | — |
| `github.packages_list_packages_for_authenticated_user` | package_type, package_type | — |

### Notifications (1 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.notifications` | — | gh api notifications |

### Pages (GitHub Pages) (1 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.pages` | owner, repo, owner, repo | — |

### Insights / metrics / activity / clones / referrers (4 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.activity` | owner, repo, owner, repo | — |
| `github.clones` | owner, repo, owner, repo | — |
| `github.metrics` | org, org | — |
| `github.views` | owner, repo, owner, repo | — |

### Copilot (1 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.copilot` | org, username, org, username | — |

### Projects v2 (1 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.projects_v2` | org, org | — |

### Enterprise / admin (1 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.enterprise_1_day` | enterprise, day, day, enterprise | — |

### Checks / status (1 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.check_runs` | owner, repo, ref, owner, ref, repo | — |

### Interactions / limits / blocks (2 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.blocked_by` | owner, repo, issue_number, issue_number, owner, repo | — |
| `github.blocking` | owner, repo, issue_number, issue_number, owner, repo | — |

### Rule suites / rulesets / branch protection (7 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.enforce_admins` | owner, repo, branch, branch, owner, repo | — |
| `github.protection` | owner, repo, branch, branch, owner, repo | — |
| `github.required_signatures` | owner, repo, branch, branch, owner, repo | — |
| `github.required_status_checks` | owner, repo, branch, branch, owner, repo | — |
| `github.restrictions` | owner, repo, branch, branch, owner, repo | — |
| `github.rule_suites` | org, org | — |
| `github.rulesets` | org, org | — |

### Forks / invitations / subscriptions (2 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.failed_invitations` | org, org | — |
| `github.invitations` | org, org | — |

### Custom / variants / codeql variants (2 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.stubbed` | — | — |
| `github.variant_analyses` | owner, repo, codeql_variant_analysis_id, codeql_variant_analysis_id, owner, repo | — |

### Other (admin / class / meta / versions / etc.) (101 tables)

| Table | Required filters | gh CLI equivalent |
|---|---|---|
| `github.accepted_assignments` | assignment_id, assignment_id | — |
| `github.access` | owner, repo, owner, repo | — |
| `github.accounts` | plan_id, plan_id | — |
| `github.analyses` | owner, repo, owner, repo | — |
| `github.annotations` | owner, repo, check_run_id, check_run_id, owner, repo | — |
| `github.assignees` | owner, repo, owner, repo | — |
| `github.assignments` | assignment_id, assignment_id | — |
| `github.attempts` | owner, repo, run_id, attempt_number, attempt_number, owner, repo, run_id | — |
| `github.attestations` | username, subject_digest, subject_digest, username | — |
| `github.authenticated_user` | — | — |
| `github.authors` | owner, repo, owner, repo | — |
| `github.autofix` | owner, repo, alert_number, alert_number, owner, repo | — |
| `github.autolinks` | owner, repo, owner, repo | — |
| `github.automated_security_fixes` | owner, repo, owner, repo | — |
| `github.budgets` | org, org | — |
| `github.builds` | owner, repo, owner, repo | — |
| `github.caches` | owner, repo, owner, repo | — |
| `github.campaigns` | org, org | — |
| `github.classroom_assignments` | classroom_id, classroom_id | — |
| `github.classrooms` | — | — |
| `github.code_frequency` | owner, repo, owner, repo | — |
| `github.codes_of_conduct` | — | — |
| `github.collaborators` | owner, repo, owner, repo | gh api repos/o/r/collaborators |
| `github.config` | org, hook_id, hook_id, org | — |
| `github.configurations` | enterprise, enterprise | — |
| `github.conflicts` | org, org | — |
| `github.content_exclusion` | org, org | — |
| `github.contents` | owner, repo, path, owner, path, repo | — |
| `github.contexts` | owner, repo, branch, branch, owner, repo | — |
| `github.custom` | org, org | — |
| `github.databases` | owner, repo, owner, repo | — |
| `github.default_setup` | owner, repo, owner, repo | — |
| `github.defaults` | enterprise, enterprise | — |
| `github.deliveries` | org, hook_id, hook_id, org | — |
| `github.downloads` | org, org | — |
| `github.emails` | — | — |
| `github.emojis` | — | — |
| `github.environments` | owner, repo, owner, repo | — |
| `github.errors` | owner, repo, owner, repo | — |
| `github.exports` | codespace_name, export_id, codespace_name, export_id | — |
| `github.feeds` | — | — |
| `github.fields` | project_number, org, org, project_number | — |
| `github.files` | owner, repo, pull_number, owner, pull_number, repo | — |
| `github.github_owned` | org, org | — |
| `github.grades` | assignment_id, assignment_id | — |
| `github.health` | owner, repo, owner, repo | — |
| `github.history` | org, ruleset_id, org, ruleset_id | — |
| `github.hovercard` | username, username | — |
| `github.import` | owner, repo, owner, repo | — |
| `github.instances` | owner, repo, alert_number, alert_number, owner, repo | — |
| `github.items` | project_number, org, org, project_number | — |
| `github.jobs` | owner, repo, run_id, owner, repo, run_id | — |
| `github.large_files` | owner, repo, owner, repo | — |
| `github.latest` | enterprise, enterprise | — |
| `github.limits` | org, org | — |
| `github.locations` | owner, repo, alert_number, alert_number, owner, repo | — |
| `github.meta` | — | — |
| `github.meta_get_all_versions` | — | — |
| `github.network_configurations` | org, org | — |
| `github.network_settings` | org, network_settings_id, network_settings_id, org | — |
| `github.new` | owner, repo, owner, repo | — |
| `github.organization_1_day` | org, day, day, org | — |
| `github.organization_roles` | org, org | — |
| `github.parent` | owner, repo, issue_number, issue_number, owner, repo | — |
| `github.participation` | owner, repo, owner, repo | — |
| `github.partner` | org, org | — |
| `github.paths` | owner, repo, owner, repo | — |
| `github.pattern_configurations` | org, org | — |
| `github.permission` | owner, repo, username, owner, repo, username | — |
| `github.permissions_check` | owner, repo, ref, devcontainer_path, devcontainer_path, owner, ref, repo | — |
| `github.platforms` | org, org | — |
| `github.profile` | owner, repo, owner, repo | — |
| `github.public_emails` | — | — |
| `github.public_key` | org, org | — |
| `github.punch_card` | owner, repo, owner, repo | — |
| `github.rate_limit` | — | gh api rate_limit |
| `github.retention_limit` | enterprise, enterprise | — |
| `github.route_stats` | org, actor_type, actor_id, min_timestamp, actor_id, actor_type, min_timestamp, org | — |
| `github.rows` | — | — |
| `github.sbom` | owner, repo, owner, repo | — |
| `github.scan_history` | owner, repo, owner, repo | — |
| `github.schema` | org, org | — |
| `github.security_managers` | org, org | — |
| `github.selected_actions` | org, org | — |
| `github.stargazers` | owner, repo, owner, repo | gh api repos/o/r/stargazers |
| `github.status` | owner, repo, ref, owner, ref, repo | — |
| `github.storage_limit` | enterprise, enterprise | — |
| `github.storage_records` | org, subject_digest, org, subject_digest | — |
| `github.subject_stats` | org, min_timestamp, min_timestamp, org | — |
| `github.summary` | org, org | — |
| `github.templates` | — | — |
| `github.user` | — | gh api user |
| `github.users` | — | gh api users/{u} |
| `github.users_1_day` | enterprise, day, day, enterprise | — |
| `github.users_list_followers_for_user` | username, username | — |
| `github.users_list_following_for_user` | username, username | — |
| `github.users_list_gpg_keys_for_user` | username, username | — |
| `github.users_list_public_keys_for_user` | username, username | — |
| `github.users_list_social_accounts_for_user` | username, username | — |
| `github.users_list_ssh_signing_keys_for_user` | username, username | — |
| `github.versions` | package_type, package_name, package_name, package_type | — |

## Notes & methodology

- Inventory taken from `coral.tables`, `coral.columns`, `coral.filters`, and `coral.table_functions` against the `github` schema.
- Required-filter lists include both static metadata-required filters and `is_required=true` filter metadata.
- gh CLI hints are best-guess mappings; not all endpoints have a one-to-one equivalent.
- Categories are heuristic (based on table-name prefixes); a few mis-grouped entries are expected.

## How to use

```sql
-- list 5 open issues in withcoral/coral
SELECT number, title, state FROM github.issues
WHERE owner='withcoral' AND repo='coral' AND state='open'
ORDER BY created_at DESC LIMIT 5;

-- list recent workflow runs
SELECT name, status, conclusion, run_number FROM github.repo_action_runs
WHERE owner='FiscalMindset' AND repo='coral'
ORDER BY created_at DESC LIMIT 5;

-- search across issues & PRs
SELECT * FROM github.search_issues('repo:withcoral/coral release');
```