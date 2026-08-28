# Team GitHub & Workflow Guide
### AI Contract Intelligence & Negotiation Assistant

**Maintained by:** GitHub & Documentation Team
**Audience:** All team members (Scrum Master, NLP/ML, Backend AI, UI/UX & Frontend, Testing, GitHub & Docs)

---

## 1. Why this guide exists

Thirteen people are going to be editing the same codebase. Without a shared process, things break in predictable ways: two people overwrite each other's work, broken code gets pushed and blocks everyone else, nobody remembers why a change was made, or a bug ships because no one double-checked it.

Everything in this guide exists to prevent one of those specific problems. Read section 2 once to understand *why* these tools exist — after that, sections 3+ are what you'll actually use day to day.

---

## 2. The Core Concepts (read this once)

| Concept | What it is | What problem it solves |
|---|---|---|
| **Branch** | A personal copy of the code you work in | Stops your unfinished/broken work from affecting anyone else |
| **`develop`** | Shared "in progress" version of the code | Lets finished features get combined and tested together before they're final |
| **`main`** | The stable, always-working version | Gives everyone one trustworthy version to build on / demo / ship |
| **Pull Request (PR)** | A request to merge your branch into `develop` | Forces a second person to check your work before it becomes shared |
| **Code Review** | Someone reading your PR before approving it | Catches bugs, spreads knowledge, keeps quality consistent across 13 people |
| **CI (`ci.yml`)** | Automated tests that run on every PR | Catches broken code automatically — computers don't forget to check, humans do |
| **Branch Protection** | GitHub-enforced rule: no merging without review/passing CI | Removes the risk of skipping review "just this once" under deadline pressure |
| **CODEOWNERS** | Auto-assigns the right reviewer based on what files changed | Nobody has to remember/guess who should review a given PR |

**The one-sentence version:** you never work directly on `main` or `develop` — you branch, do your work, open a PR, get it reviewed, and only then does it join the shared codebase.

---

## 3. One-Time Setup (do this once)

1. **Get added as a collaborator** on the repo (GitHub/Docs lead will add your username).
2. **Clone the repo locally:**
   ```bash
   git clone https://github.com/<org-or-username>/<repo-name>.git
   cd <repo-name>
   ```
3. **Set your Git identity** (if not already set on your machine):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```
4. **Switch to `develop`** — this is your base branch, not `main`:
   ```bash
   git checkout develop
   git pull origin develop
   ```

---

## 4. Daily Workflow (what you'll actually do, every time)

### Step 1 — Start from an up-to-date `develop`
```bash
git checkout develop
git pull origin develop
```
*Why: if you branch off a stale `develop`, you'll get avoidable merge conflicts later.*

### Step 2 — Create your branch
Use the naming convention so anyone can tell what a branch is for at a glance:

| Prefix | Use for | Example |
|---|---|---|
| `feature/` | New functionality | `feature/clause-comparison-view` |
| `fix/` | Bug fixes | `fix/pdf-upload-timeout` |
| `hotfix/` | Urgent fix on live/`main` code | `hotfix/auth-token-leak` |
| `chore/` | Config, tooling, dependencies | `chore/update-ci-python-version` |
| `docs/` | Documentation only | `docs/update-readme-setup` |

```bash
git checkout -b feature/your-branch-name
```

### Step 3 — Do your work, commit as you go
Don't wait until everything is finished to commit — commit in small, logical chunks.

**Commit message format** ([Conventional Commits](https://www.conventionalcommits.org)):
```
<type>(<scope>): <short summary>
```
Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Examples:
```
feat(ml): add clause risk scoring model
fix(backend): handle malformed contract upload gracefully
docs(readme): add local setup instructions
```
*Why: consistent messages make the project history and changelog actually readable later — "fixed stuff" tells no one anything in three weeks.*

```bash
git add .
git commit -m "feat(ml): add clause risk scoring model"
```

### Step 4 — Keep your branch up to date (do this regularly, not just at the end)
```bash
git fetch origin
git rebase origin/develop
```
*Why: the longer your branch diverges from `develop`, the worse your eventual merge conflicts get. Rebasing often keeps conflicts small and manageable instead of one huge mess at the end.*

### Step 5 — Push your branch
```bash
git push -u origin feature/your-branch-name
```

### Step 6 — Open a Pull Request
On GitHub: **Pull requests → New pull request** → base = `develop`, compare = your branch.

Fill out the PR template completely:
- What changed and why
- Linked issue (`Closes #12`)
- How you tested it
- Checklist (no secrets committed, tests added, docs updated)

*Why the template: reviewers shouldn't have to ask "what does this actually do?" — the template front-loads that.*

### Step 7 — Wait for CI + review
- CI runs automatically — you'll see checks appear on the PR page.
- CODEOWNERS auto-requests the right reviewer(s) based on which folders you touched.
- Respond to review comments, push additional commits to the same branch if changes are requested (no need to open a new PR).

### Step 8 — Merge
Once approved and CI passes, **squash and merge** into `develop` (keeps history clean — your 15 small commits become one clean entry).

### Step 9 — Clean up
```bash
git checkout develop
git pull origin develop
git branch -d feature/your-branch-name
```

---

## 5. How to Review Someone Else's PR

If CODEOWNERS or a teammate asks you to review:

1. Open the **Files changed** tab on the PR
2. Ask yourself:
   - Does this actually do what the PR description says?
   - Is there an obvious bug or edge case missed?
   - Does it follow the naming/structure conventions the rest of the code uses?
   - Are there tests, if the change needs them?
   - Anything that looks like a secret, API key, or real contract data accidentally committed?
3. Leave comments directly on specific lines for anything unclear or wrong
4. Either:
   - **Approve** — if it's good to merge
   - **Request changes** — if something needs fixing first (be specific, suggest a fix, don't just say "this is wrong")
5. Respond within **1 business day** where possible — a PR sitting unreviewed for a week blocks the author from moving forward.

*Why this matters: review isn't a formality — it's the actual mechanism that catches bugs before 12 other people are relying on broken code.*

---

## 6. Merge Conflicts — what to do when Git says "conflict"

This happens when two people changed the same lines in a file. It's normal, not a mistake.

```bash
git fetch origin
git rebase origin/develop
```

Git will pause and mark the conflicting file like this:
```
<<<<<<< HEAD
your version of the code
=======
the incoming version of the code
>>>>>>> origin/develop
```

1. Open the file, decide what the final version should look like (sometimes it's one side, sometimes it's a merge of both)
2. Delete the `<<<<<<<`, `=======`, `>>>>>>>` markers
3. Save, then:
   ```bash
   git add <the file>
   git rebase --continue
   ```
4. If the conflict is non-trivial (not just formatting — actual overlapping logic), **talk to the other author** before guessing. Don't silently pick one side.
5. Push:
   ```bash
   git push --force-with-lease
   ```
   *(force-with-lease is required after a rebase — it's safe because it refuses to overwrite anyone else's work you haven't seen.)*

**Best prevention:** rebase onto `develop` often (Step 4 above), so conflicts stay small instead of piling up over two weeks.

---

## 7. Role-Specific Guide

### Scrum Master
- Doesn't need to commit code, but should understand PRs enough to **close linked issues** once a PR is merged (approving completed user stories)
- Track sprint progress via GitHub **Issues** and **Milestones** — one milestone per sprint, issues assigned to it
- Use the PR list to gauge real sprint progress (open vs. merged) alongside the burndown chart

### NLP & ML Team
- Work in `/ml/`
- Document model choices, prompt versions, and evaluation results in `/docs/` as you go — not just in code comments, since this affects how Backend integrates with you

### Backend AI Team
- Work in `/backend/`
- Document new API endpoints (even briefly) in the PR description — Frontend needs to know what's available without reading your code
- Any change to authentication or database schema should be flagged clearly in the PR title/description — these are the changes most likely to break other teams' work

### UI/UX & Frontend Team
- Work in `/frontend/`
- Include a screenshot or short clip in the PR for any visual change (the PR template has a section for this)
- Coordinate with Backend early on API shape — don't build against an endpoint that doesn't exist yet without checking

### Testing Team
- Work primarily in `/tests/`, but your review role spans everything
- Recommended: **Testing team reviews/signs off before a PR merges into `develop`**, not just when `/tests/` itself is touched — since your job is catching what the author missed
- Bug reports go in GitHub **Issues** using the bug report template, not Slack/WhatsApp — so they're tracked and don't get lost
- Log hallucination/prompt-testing results in `/docs/` so ML team can reference them across sprints, not just in a one-off chat message

### GitHub & Documentation (you)
- Keep README, CHANGELOG, and CODEOWNERS accurate as the team and stack evolve
- Spot-check that people are following branch naming and PR process
- Own `/docs/sprints/`, `/docs/meetings/`, `/docs/releases/`
- Tag releases and write release notes at each milestone

---

## 8. Sprint & Meeting Documentation

*(Templates for these will be added to `/docs/sprints/` and `/docs/meetings/` — see the GitHub & Docs lead for the current template.)*

General rule: every sprint planning session, stand-up summary (weekly, not daily, is usually enough to log), review, and retro should leave a written trace in `/docs/`. If it's not written down, it didn't happen as far as anyone joining later is concerned.

---

## 9. Quick Command Reference

```bash
# Start new work
git checkout develop && git pull origin develop
git checkout -b feature/my-feature

# Save work
git add .
git commit -m "feat(scope): summary"

# Stay up to date / avoid conflicts
git fetch origin
git rebase origin/develop

# Push
git push -u origin feature/my-feature
# (after a rebase, use:)
git push --force-with-lease

# After merge, clean up
git checkout develop && git pull origin develop
git branch -d feature/my-feature
```

---

## 10. FAQ

**"Can I just push straight to `main` or `develop` to save time?"**
No — this is the one rule that shouldn't be broken even under deadline pressure. It's exactly the situation branch protection exists for. If GitHub isn't yet enforcing it technically (private repo, no Student Pack yet), it's still a firm team agreement.

**"My PR has been open for 3 days with no review."**
Ping the reviewer directly, or flag it to the GitHub & Docs lead to nudge/reassign.

**"I don't know who should review my PR."**
You shouldn't need to — CODEOWNERS auto-assigns based on the folder you changed. If no one gets auto-assigned, flag it; the CODEOWNERS file needs updating.

**"CI failed on my PR but I don't understand why."**
Click into the failed check on the PR page — it shows the exact error. If it's unclear, ask in the team channel rather than force-merging around it.

**"I broke something on my branch and want to start over."**
```bash
git checkout develop
git branch -D feature/broken-branch
git checkout -b feature/broken-branch-v2
```
Nothing is lost from `develop` — only your local branch is discarded.
