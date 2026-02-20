# Git Workflow

> If your project has a `project-implementation.md` rule, check it for framework-specific overrides.

## Remotes

Configure remotes in your project's `project-implementation.md`. Standard setup:

| Remote | URL | Purpose |
|--------|-----|---------|
| `origin` | Your repository | Primary development |

## Branch Strategy

| Branch | Purpose | Pushes To |
|--------|---------|-----------|
| `development` | Active working branch -- all daily work lands here | `origin/development` |
| `main` | Stable branch -- CI runs here, deploy candidates | `origin/main` |

All daily development happens on `development`. Use PRs from `development` to `main` when ready to trigger CI and prepare a release.

## Commit Message Format

```
<type>(<scope>): <description>

<optional body>
```

| Field | Values |
|-------|--------|
| **type** | `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci` |
| **scope** | App name or feature area (e.g., `auth`, `dashboard`, `billing`) |

## Before Pushing

Run your verification suite as a pre-push gate. Skipping it means broken code reaches `origin`:

```bash
pnpm verify   # typecheck + lint + test
```

If verify fails, fix issues before pushing.

## CI Pipeline

Standard CI jobs for Next.js/Supabase projects:

| CI Job | What it does | Timeout |
|--------|-------------|---------|
| TypeScript | `typecheck` + `lint` | 10 min |
| Unit Tests | `pnpm test` | 10 min |
| E2E Tests | Playwright (if enabled) | 20 min |

## Pull Request Workflow

When creating PRs:

1. Analyze full commit history (not just latest commit)
2. Use `git diff [base-branch]...HEAD` to see all changes
3. Draft comprehensive PR summary
4. Include test plan with TODOs
5. Push with `-u` flag if new branch

## Feature Implementation Workflow

1. **Plan** -- Use `/create-plan` to generate phases and structure
2. **Review Plan** -- Use `/review-plan` to verify each phase
3. **Implement** -- Use `/implement` to execute phases (handles TDD, coding, review loop)
4. **Code Review** -- Use `/code-review` after implementation to verify quality
5. **Verify** -- Run `pnpm verify` before committing
6. **Commit** -- Follow conventional commits format with scope
