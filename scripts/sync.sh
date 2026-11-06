set -e

echo "Starting Main Repo ML-Core to Web-Dev Branch Safe Sync..."

git config --global user.name "DevBridge Main Sync Bot"
git config --global user.email "bot@devbridge.main"

git fetch origin

TARGET_WEB="web-dev"

# 1. Create or switch to the target web branch safely
if ! git ls-remote --exit-code --heads origin $TARGET_WEB; then
  git checkout -b $TARGET_WEB
  git push origin $TARGET_WEB
fi

# 2. Setup a temporary synchronization branch based on origin/$TARGET_WEB
git checkout main
git checkout -b temp-web-sync origin/$TARGET_WEB || git checkout -b temp-web-sync

# 3. Pull ONLY the 'ml' folder from main into the temp branch
# This overlays or updates 'ml' without affecting backend, frontend, etc.
git checkout main -- ml/

# 4. Stage and commit only the changes made to 'ml/'
git add ml/
git commit -m "chore(sync): seamlessly update shared ml/ core from main" || echo "No changes to ml/ folder"

# 5. Push safely to the target web-dev branch
git push origin temp-web-sync:$TARGET_WEB --force

# 6. Cleanup local temporary branch
git checkout main
git branch -D temp-web-sync 2>/dev/null || true

echo "Web branch sync completed successfully! Backend and frontend directories remain untouched."