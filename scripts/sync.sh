set -e

echo "Starting Fork-Side Dual-Mobile & ML-Core Sync..."

git config --global user.name "DevBridge Mobile Sync Bot"
git config --global user.email "bot@devbridge.fork"

git stash --include-untracked || true

git fetch origin --prune

TARGET_MOB1="mob-dev1"

if ! git ls-remote --exit-code --heads origin $TARGET_MOB1; then
  echo "Creating remote $TARGET_MOB1 from main..."
  git checkout main
  git checkout -b $TARGET_MOB1
  git push origin $TARGET_MOB1
fi

git checkout -b temp-mob1-sync origin/$TARGET_MOB1 || git checkout -b temp-mob1-sync origin/$TARGET_MOB1 2>/dev/null || git checkout -b temp-mob1-sync
git checkout main -- ml/ 2>/dev/null || true

git add ml/ mobile/ 2>/dev/null || true
git commit -m "chore(sync): updated shared ml/ core for mob-dev1" || echo "No changes for mob-dev1"
git push origin temp-mob1-sync:$TARGET_MOB1 --force

TARGET_MOB2="mob-dev2"

if ! git ls-remote --exit-code --heads origin $TARGET_MOB2; then
  echo "Creating remote $TARGET_MOB2 from $TARGET_MOB1..."
  git checkout -b $TARGET_MOB1 origin/$TARGET_MOB1 || git checkout $TARGET_MOB1
  git checkout -b $TARGET_MOB2
  git push origin $TARGET_MOB2
fi

git checkout -b temp-mob2-sync origin/$TARGET_MOB2 || git checkout -b temp-mob2-sync origin/$TARGET_MOB2 2>/dev/null || git checkout -b temp-mob2-sync
git checkout main -- ml/ 2>/dev/null || true

git add ml/ mobile/ 2>/dev/null || true
git commit -m "chore(sync): updated shared ml/ core for mob-dev2 (preserving unique UI & features)" || echo "No changes for mob-dev2"
git push origin temp-mob2-sync:$TARGET_MOB2 --force

git checkout main
git branch -D temp-mob1-sync temp-mob2-sync 2>/dev/null || true

echo "Fork-side dual-mobile sync completed successfully!"