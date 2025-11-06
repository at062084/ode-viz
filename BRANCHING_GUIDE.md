# Understanding Branches with Claude Code on GitHub

## Current Situation

Your repository **only has Claude branches** right now:
- `claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM` ← Your current work
- `claude/docker-apache-superset-011CUrr1qBmXmLGZc7Df7LEb` ← Earlier session

**There is no `main` or `master` branch yet!**

## How Claude Code Branches Work

### 1. Session Branches
When Claude Code works on a task, it creates a branch with this pattern:
```
claude/<description>-<session-id>
```

Example: `claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM`
- `github-action-superset-build` = descriptive name
- `011CUruagQwpnbseTBYBssqM` = unique session ID

### 2. Why Session IDs?
- **Isolation**: Each task gets its own branch
- **Safety**: Changes don't affect main branch until you approve
- **Review**: You can review changes before merging
- **Parallel work**: Multiple Claude sessions can work simultaneously

## Setting Up a Main Branch

You have two options:

### Option 1: Create Main Branch from Current Work (Recommended)

Since your current branch has all the latest work, make it the main branch:

```bash
# On your PULPHOST or local machine
cd ~/ode-viz  # or wherever your repo is

# Create main branch from current branch
git checkout -b main
git push -u origin main

# Set main as default branch on GitHub
# (see GitHub Web UI steps below)
```

### Option 2: Via GitHub Web UI

1. Go to: https://github.com/at062084/ode-viz
2. Click the **branch dropdown** (shows current branch)
3. Type `main` and click "Create branch: main from claude/github-action..."
4. Go to **Settings** → **Branches**
5. Set `main` as the default branch

## Recommended Workflow

### Step 1: Create Main Branch

```bash
# Checkout your current Claude branch (if not already on it)
git checkout claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM

# Create and push main branch
git checkout -b main
git push -u origin main
```

### Step 2: Set as Default on GitHub

1. Go to: https://github.com/at062084/ode-viz/settings
2. Click **Branches** in left sidebar
3. Under "Default branch", click the switch icon
4. Select `main`
5. Click "Update"

### Step 3: Future Workflow

Now that you have a main branch:

```
main (stable, production-ready)
  │
  ├── claude/feature-1-session123 (Claude works here)
  ├── claude/feature-2-session456 (Claude works here)
  └── claude/bugfix-3-session789 (Claude works here)
```

**When a Claude session finishes:**
1. Review the changes
2. Test the code
3. Merge to main (via Pull Request or direct merge)
4. Delete the Claude branch (optional)

## Merging Claude Branches to Main

### Via GitHub Pull Request (Recommended)

1. Go to: https://github.com/at062084/ode-viz/pulls
2. Click **New pull request**
3. Select:
   - Base: `main`
   - Compare: `claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM`
4. Review changes
5. Click **Create pull request**
6. Click **Merge pull request**

### Via Command Line

```bash
# Switch to main
git checkout main

# Merge the Claude branch
git merge claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM

# Push to GitHub
git push origin main

# Optional: Delete old Claude branch
git branch -d claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM
git push origin --delete claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM
```

## Quick Setup Commands

**Copy-paste these commands to set up main branch now:**

```bash
# 1. Checkout your current Claude branch
git checkout claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM

# 2. Create main branch from here
git checkout -b main

# 3. Push it to GitHub
git push -u origin main

# 4. Verify
git branch -a
# Should now show 'main' branch
```

Then go to GitHub and set `main` as default branch in Settings → Branches.

## Comparing to GitLab

| GitLab | GitHub + Claude |
|--------|-----------------|
| `main` or `master` created automatically | No main branch initially |
| Work in feature branches | Claude creates session branches |
| Merge via Merge Request | Merge via Pull Request or git merge |
| Can set default branch | Set in Settings → Branches |

**The main difference:** Claude Code doesn't create a main branch automatically. You need to create it from one of the Claude branches.

## Current Branch Structure

```
Your Repository (at062084/ode-viz)
├── claude/docker-apache-superset-011CUrr1qBmXmLGZc7Df7LEb (older)
└── claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM (current, latest)

After setting up main:
├── main (stable) ← Set this as default!
├── claude/docker-apache-superset-011CUrr1qBmXmLGZc7Df7LEb
└── claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM
```

## What You Should Do Now

1. **Create main branch** from your current Claude branch (it has all the latest code)
2. **Set main as default** on GitHub
3. **Test your deployment** (run docker compose up)
4. **Keep working** - Future Claude sessions will work from main

## Benefits of This Workflow

✅ **Safe**: Changes isolated until you approve
✅ **Reviewable**: See exactly what changed
✅ **Trackable**: Each task has its own branch
✅ **Clean**: Main branch stays stable
✅ **Flexible**: Work on multiple features in parallel

## Still Confused?

Think of it this way:
- **Claude branches** = Working branches (like feature branches in GitLab)
- **main branch** = Stable branch (like main/master in GitLab)
- **You decide** when to merge Claude's work into main

The only difference: You need to create the main branch first since this is a new repo!
