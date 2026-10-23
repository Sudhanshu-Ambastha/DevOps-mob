set -e

echo "Starting Fork-Side Mobile Sync (mob-dev & mob-dev2)..."

git config --global user.name "DevBridge Mobile Sync Bot"
git config --global user.email "bot@devbridge.fork"

git stash --include-untracked || true

git fetch origin --prune

TARGET_MOB="mob-dev"

if ! git ls-remote --exit-code --heads origin $TARGET_MOB; then
  echo "Creating remote $TARGET_MOB from main..."
  git checkout main
  git checkout -b $TARGET_MOB
  git push origin $TARGET_MOB
fi

git checkout -b temp-mob-sync origin/$TARGET_MOB || git checkout -b temp-mob-sync origin/$TARGET_MOB 2>/dev/null || git checkout -b temp-mob-sync
git checkout main -- ml/ 2>/dev/null || true

git add ml/ mobile/ 2>/dev/null || true
git commit -m "chore(sync): updated shared ml/ core for mob-dev" || echo "No changes for mob-dev"
git push origin temp-mob-sync:$TARGET_MOB --force

TARGET_MOB2="mob-dev2"

if ! git ls-remote --exit-code --heads origin $TARGET_MOB2; then
  echo "Creating remote $TARGET_MOB2 from $TARGET_MOB..."
  git checkout -b $TARGET_MOB origin/$TARGET_MOB || git checkout $TARGET_MOB
  git checkout -b $TARGET_MOB2
  git push origin $TARGET_MOB2
fi

git checkout -b temp-mob2-sync origin/$TARGET_MOB2 || git checkout -b temp-mob2-sync origin/$TARGET_MOB2 2>/dev/null || git checkout -b temp-mob2-sync
git checkout main -- ml/ 2>/dev/null || true

git add ml/ mobile/ 2>/dev/null || true
git commit -m "chore(sync): updated shared ml/ core for mob-dev2 (preserving unique UI & features)" || echo "No changes for mob-dev2"
git push origin temp-mob2-sync:$TARGET_MOB2 --force

git checkout main
git branch -D temp-mob-sync temp-mob2-sync 2>/dev/null || true

echo "Fork-side sync completed successfully! Only mob-dev and mob-dev2 are active."