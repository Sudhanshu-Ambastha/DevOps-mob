set -e

echo "Starting Multi-Branch ML-Core & .gitignore Smart Sync..."

git config --global user.name "DevBridge Main Sync Bot"
git config --global user.email "bot@devbridge.main"

git fetch origin

# Define all target branches you want to keep updated (only if they exist)
TARGET_BRANCHES=("web-dev" "mob-dev" "mob-dev2")

for TARGET in "${TARGET_BRANCHES[@]}"; do
    echo "--------------------------------------------------"
    echo "Checking branch: $TARGET"

    # Check if the branch actually exists on remote (origin)
    if git ls-remote --exit-code --heads origin "$TARGET" > /dev/null 2>&1; then
        echo "Branch '$TARGET' found. Proceeding with sync..."

        # 1. Setup a temporary synchronization branch based on origin/$TARGET
        git checkout main
        TEMP_SYNC="temp-sync-$TARGET"
        git checkout -b "$TEMP_SYNC" origin/"$TARGET" || git checkout -b "$TEMP_SYNC"

        # 2. Pull ONLY the 'ml/' folder and '.gitignore' from main
        git checkout main -- ml/
        git checkout main -- .gitignore

        # 3. Smart-merge .gitignore if it already exists on the target branch
        if [ -f .gitignore ]; then
            echo "Merging .gitignore rules for $TARGET..."
            sort -u .gitignore > .gitignore.merged
            mv .gitignore.merged .gitignore
        fi

        # 4. Stage and commit only ml/ and the merged .gitignore
        git add ml/ .gitignore
        git commit -m "chore(sync): seamlessly update shared ml/ core and merge .gitignore from main" || echo "No changes to sync for $TARGET"

        # 5. Push safely to the target branch
        git push origin "$TEMP_SYNC":"$TARGET" --force

        # 6. Cleanup local temporary branch
        git checkout main
        git branch -D "$TEMP_SYNC" 2>/dev/null || true

        echo "Successfully synced branch: $TARGET"
    else
        echo "Branch '$TARGET' does not exist on remote. Skipping..."
    fi
done

echo "--------------------------------------------------"
echo "All branch sync operations completed successfully!"
