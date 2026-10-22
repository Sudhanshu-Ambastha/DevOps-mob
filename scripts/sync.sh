#!/bin/bash
set -e

echo "Starting DevBridge ML-Core Only Sync..."

# Configure Git Identity
git config --global user.name "DevBridge ML Sync Bot"
git config --global user.email "bot@devbridge.fork"

git fetch origin

# -------------------------------------------------------------------------
# 1. SYNC WEB BRANCH (SSG, PS)
# Pulls only updated ml/ from main into web-dev, leaving web/ untouched.
# -------------------------------------------------------------------------
TARGET_WEB="web-dev"

if ! git ls-remote --exit-code --heads origin $TARGET_WEB; then
  git checkout -b $TARGET_WEB
  git push origin $TARGET_WEB
fi

git checkout main
git checkout -b temp-web-sync origin/$TARGET_WEB || git checkout -b temp-web-sync

# Pull ONLY the ml/ folder from main
git checkout main -- ml/ 2>/dev/null || true

git add ml/ web/ 2>/dev/null || true
git commit -m "chore(sync): updated shared ml/ core for Web Team" || echo "No changes for web"
git push origin temp-web-sync:$TARGET_WEB --force

# -------------------------------------------------------------------------
# 2. SYNC MOBILE BRANCH (AS, SA, KR, AA)
# Pulls only updated ml/ from main into mob-dev, leaving mobile/ untouched.
# -------------------------------------------------------------------------
TARGET_MOBILE="mob-dev"

if ! git ls-remote --exit-code --heads origin $TARGET_MOBILE; then
  git checkout main
  git checkout -b $TARGET_MOBILE
  git push origin $TARGET_MOBILE
fi

git checkout main
git checkout -b temp-mob-sync origin/$TARGET_MOBILE || git checkout -b temp-mob-sync

# Pull ONLY the ml/ folder from main
git checkout main -- ml/ 2>/dev/null || true

git add ml/ mobile/ 2>/dev/null || true
git commit -m "chore(sync): updated shared ml/ core for Mobile Team" || echo "No changes for mobile"
git push origin temp-mob-sync:$TARGET_MOBILE --force

# Cleanup temporary sync branches locally
git checkout main
git branch -D temp-web-sync temp-mob-sync 2>/dev/null || true

echo "ML-Core sync completed successfully!"