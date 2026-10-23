set -e

echo "Starting Main Repo ML-Core to Web Sync..."

git config --global user.name "DevBridge Main Sync Bot"
git config --global user.email "bot@devbridge.main"

git fetch origin

TARGET_WEB="web-dev"

if ! git ls-remote --exit-code --heads origin $TARGET_WEB; then
  git checkout -b $TARGET_WEB
  git push origin $TARGET_WEB
fi

git checkout main
git checkout -b temp-web-sync origin/$TARGET_WEB || git checkout -b temp-web-sync

git checkout main -- ml/ 2>/dev/null || true

git add ml/ web/ 2>/dev/null || true
git commit -m "chore(sync): updated shared ml/ core for Web Team" || echo "No changes for web"
git push origin temp-web-sync:$TARGET_WEB --force

git checkout main
git branch -D temp-web-sync 2>/dev/null || true

echo "Main repo web sync completed successfully!"