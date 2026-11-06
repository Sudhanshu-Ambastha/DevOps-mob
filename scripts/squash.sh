# 1. Switch to your mob-dev branch and ensure it's up to date
git checkout mob-dev
git pull origin mob-dev

# 2. Create a temporary orphan branch to wipe out all messy commit history
git checkout --orphan temp-mob-squash

# 3. Stage all current files cleanly
git add -A

# 4. Commit everything as a single clean initial commit
git commit -m "chore(mob-dev): initial consolidated release for mobile development"

# 5. Delete your old local mob-dev branch
git branch -D mob-dev

# 6. Rename this temporary branch to mob-dev
git branch -m mob-dev

# 7. Force push the completely flattened mob-dev branch to your fork's remote origin
git push origin mob-dev --force-with-lease