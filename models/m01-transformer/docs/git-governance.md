# Git governance

This repository uses a small set of rules to keep large changes reviewable and safe.

## Quick path

1. Create a worktree for the change.
2. Use conventional commits, one work unit per commit.
3. Keep tests and docs with the behavior they describe.
4. Open PRs with the issue link and one `type:*` label.

## Branch model

| Branch | Purpose |
|---|---|
| `main` | Stable integration branch |
| `feat/*` | New behavior |
| `fix/*` | Bug fixes |
| `docs/*` | Documentation only |
| `chore/*` | Tooling, cleanup, maintenance |
| `refactor/*` | Structural code changes without behavior drift |

## Worktrees

- Prefer one worktree per active task.
- Keep worktrees near the repo, not in temp folders.
- Name them after the branch or work unit.

## Commit rules

- One commit = one deliverable unit.
- Commit message must be conventional.
- Keep tests with the code they verify.
- Prefer reversible slices over giant mixed diffs.

## PR rules

- Link an approved issue.
- Add exactly one `type:*` label.
- Explain what changed, how it was verified, and how to roll it back.
- Split oversized work into chained PRs when needed.

## Archive policy

- Put stale, local-only, or nonfunctional material under `archive/`.
- Do not archive active runtime code, checkpoints, or live data without a separate migration plan.
- Keep archived files byte-identical unless the migration explicitly requires otherwise.

## Hooks

Run `scripts/git/setup-hooks.ps1` once per clone to enable local hooks and the commit template.

## Checklist

- [ ] Hooks enabled
- [ ] Worktree created
- [ ] Branch follows the naming rule
- [ ] Commit message is conventional
- [ ] PR links an issue
