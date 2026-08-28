# Contributing Guide

This document defines how we branch, commit, review, and release code for the AI Contract Intelligence & Negotiation Assistant. Following it consistently keeps `main` stable and makes the history easy to audit — which matters especially for a project handling legal/contract data.

## Branch Strategy

We use a **GitHub Flow**-based model with three long-lived/protected branches:

| Branch | Purpose |
|---|---|
| `main` | Always deployable / production-ready |
| `develop` | Integration branch for the current sprint |
| `release/*` | Cut from `develop` when preparing a release |

**Working branches** (created off `develop`, deleted after merge):

| Prefix | Use case | Example |
|---|---|---|
| `feature/` | New functionality | `feature/clause-comparison-view` |
| `fix/` | Bug fixes | `fix/pdf-upload-timeout` |
| `hotfix/` | Urgent production fix (branched from `main`) | `hotfix/auth-token-leak` |
| `chore/` | Tooling, deps, config, non-code changes | `chore/update-ci-node-version` |
| `docs/` | Documentation-only changes | `docs/update-readme-setup` |

**Rule of thumb:** branch off `develop`, keep branches short-lived (a few days, not weeks), and rebase on `develop` regularly to minimize merge conflicts.

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]
[optional footer, e.g. Closes #42]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**
```
feat(ml): add clause risk scoring model
fix(backend): handle malformed contract upload gracefully
docs(readme): add local setup instructions
```

Why: consistent commit messages make `CHANGELOG.md` generation possible (semi-)automatically and make `git log` actually useful for tracing when/why something changed.

## Pull Request Process

1. Branch off `develop` using the naming convention above.
2. Keep PRs small and focused — one feature/fix per PR.
3. Fill out the PR template completely (what changed, why, how it was tested, linked issue).
4. Ensure CI checks pass before requesting review.
5. Require at least **1 approving review** (2 for changes touching `ml/` risk-scoring logic, given its impact on negotiation output).
6. Squash-merge into `develop` once approved. Use `develop` → `release/*` → `main` promotion for shipping.

## Code Review Expectations

- Reviewers respond within 1 business day.
- Focus on correctness, security (esp. handling of contract/user data), readability, and test coverage.
- Be specific and constructive in comments — suggest an alternative, don't just flag a problem.
- Author resolves all conversations before merge; re-request review after major changes.

## Merge Conflicts

- Rebase your branch on the latest `develop` **before** opening a PR, and again if `develop` moves significantly while your PR is open:
  ```
  git fetch origin
  git rebase origin/develop
  ```
- If a conflict is non-trivial (e.g., overlapping logic changes, not just formatting), talk to the other author directly rather than guessing intent.
- Never resolve a conflict by blindly accepting "ours" or "theirs" — read both sides.

## Versioning

We follow [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

- **MAJOR** — breaking changes (e.g., API contract changes)
- **MINOR** — new backward-compatible features
- **PATCH** — backward-compatible bug fixes

Every merge into `main` via a release should be tagged (`git tag v1.2.0`) and documented in `CHANGELOG.md`.

## Handling Sensitive Data

This project deals with contract content, which may be confidential or legally sensitive. Never commit:
- Real/sample contract files with actual company or client data
- API keys or credentials (use `.env`, which is gitignored)
- Any user-uploaded documents

Use synthetic/anonymized contract samples for testing and demos.
