# Git Workflow

## Remotes

<!-- CUSTOMIZE: Configure your git remotes.

| Remote | URL | Purpose |
|--------|-----|---------|
| `origin` | `github.com/{your-org}/{your-repo}.git` | Your repository |
| `upstream` | (optional) | Third-party template source for updates |
-->

## Branch Strategy

| Branch | Purpose | Pushes To |
|--------|---------|-----------|
| `development` | Active working branch — all daily work lands here | `origin/development` |
| `main` | Stable branch — CI runs here, deploy candidates | `origin/main` |

<!-- CUSTOMIZE: Adjust branch names and strategy to match your team's workflow.
Some teams use `dev`/`staging`/`main`, others use feature branches with PRs to `main`. -->

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

<!-- CUSTOMIZE: Replace with your project's verify command. -->

```bash
npm run verify   # typecheck + lint + test
```

If verify fails, fix issues before pushing.

## CI Pipeline

<!-- CUSTOMIZE: Update to match your CI configuration.

Typical CI jobs for Next.js/Supabase projects:

| CI Job | What it does | Timeout |
|--------|-------------|---------|
| TypeScript | `typecheck` + `lint` | 10 min |
| Unit Tests | `npm test` | 10 min |
| E2E Tests | Playwright | 20 min |
-->

## Pull Request Workflow

When creating PRs:

1. Analyze full commit history (not just latest commit)
2. Use `git diff [base-branch]...HEAD` to see all changes
3. Draft comprehensive PR summary
4. Include test plan with TODOs
5. Push with `-u` flag if new branch

## Upstream Merge Process (Template Updates)

<!-- CUSTOMIZE: If you forked a SaaS template, document your merge process here.

Key steps:
1. `git fetch upstream`
2. Check what changed: `git log --oneline $(git merge-base development upstream/main)..upstream/main`
3. Create merge branch: `git checkout -b merge/upstream-<version> development`
4. Merge: `git merge upstream/main --no-commit`
5. Resolve conflicts (prioritize upstream for infrastructure, keep yours for custom features)
6. Verify and commit

If you have multiple product apps forked from the same template, remember to propagate
infrastructure changes to ALL apps, not just the primary one.
-->

## Feature Implementation Workflow

1. **Plan** — Use `/create-plan` to generate phases and structure
2. **Review Plan** — Use `/review-plan` to verify each phase
3. **Implement** — Use `/implement` to execute phases (handles TDD, coding, review loop)
4. **Code Review** — Use `/code-review` after implementation to verify quality
5. **Verify** — Run verification suite before committing
6. **Commit** — Follow conventional commits format with scope
