# How to Create Main Branch

## Quick Instructions

I hit a restriction: Claude Code can only push to branches that start with `claude/` and end with the session ID (for security). So **you** need to create the `main` branch.

## Option 1: Via GitHub Web UI (Easiest - 30 seconds)

1. Go to: **https://github.com/at062084/ode-viz**
2. Click the **branch dropdown** (top left, currently shows `claude/github-action-superset-build-...`)
3. Type: `main`
4. Click: **"Create branch: main from 'claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM'"**
5. Go to **Settings** → **Branches** → Set `main` as default branch

Done! ✅

## Option 2: Via Command Line (On Your Machine)

```bash
# Clone or cd to your repo
cd ~/ode-viz  # or wherever

# Fetch the latest
git fetch origin

# Create main from the Claude branch
git checkout -b main origin/claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM

# Push main
git push -u origin main
```

## After Creating Main

Once you have a `main` branch:
- I'll continue working on `claude/*` branches
- You can work on your own branches
- GitHub Actions workflow is already configured to deploy from `main`
- You can merge my Claude branches into main when ready

## GitHub Actions Workflow

The workflow is currently set to trigger on push to `main` or `master`:

```yaml
on:
  push:
    branches:
      - main
      - master
```

So once you create `main` and push to it, deployments will happen automatically!

## Summary

**What you need to do:**
1. Create `main` branch from `claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM` (use Option 1 above - takes 30 seconds)
2. Set it as default branch in GitHub Settings
3. That's it!

**What happens next:**
- I continue working on `claude/*` branches as usual
- You review and merge to `main` when ready
- Deployments happen automatically from `main`
