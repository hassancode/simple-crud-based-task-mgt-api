---
name: commit-and-push
description: Commit changes using Conventional Commits format and push to remote. Use when user asks to commit, commit changes, push code, save to git, or invokes /commit-and-push. Automatically checks for remote origin and prompts user if missing. (user)
---

# Commit and Push

Commit all changes with Conventional Commits message and push to remote.

## Workflow

1. Run `git status` and `git diff` to review changes
2. Run `git remote -v` to check for remote origin
   - **If no origin**: Ask user "No remote origin set. Please provide the git remote URL:" then run `git remote add origin <provided-url>`
3. Stage changes with `git add -A`
4. Compose Conventional Commits message
5. Commit and push with `git push -u origin HEAD`

## Conventional Commits

Format: `<type>(<scope>): <subject>`

**Types:** `feat` | `fix` | `docs` | `style` | `refactor` | `test` | `chore`

**Rules:**
- Subject: imperative, lowercase, no period, max 50 chars
- Scope: optional (e.g., `feat(auth):`)

## Commit Command

```bash
git add -A && git commit -m "$(cat <<'EOF'
type(scope): subject

Body if needed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)" && git push -u origin HEAD
```

## Safety

- Never commit `.env`, credentials, or API keys
- Warn if sensitive files are staged
- On push failure: `git pull --rebase` then retry
