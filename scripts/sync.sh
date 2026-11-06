#!/usr/bin/env bash
set -euo pipefail

SRC_REF="${SRC_REF:-origin/main}"          # where ml/ + .gitignore come from
SYNC_DIR="${SYNC_DIR:-ml}"
read -ra TARGETS <<< "${TARGETS:-web-dev}" # space-separated target branches
BRIDGE_FROM="${BRIDGE_FROM:-}"             # e.g. mob-dev   (optional)
BRIDGE_TO="${BRIDGE_TO:-}"                 # e.g. mob-dev2  (optional)
BRIDGE_DIR="${BRIDGE_DIR:-devbridge}"
MSG_TAG="chore(sync)"

git config user.name  "DevBridge Main Sync Bot"
git config user.email "bot@devbridge.main"
git fetch origin --prune

branch_exists() { git ls-remote --exit-code --heads origin "$1" >/dev/null 2>&1; }

# Union of target's rules + main's rules: keeps order, drops duplicate lines,
# keeps blank lines (squeezed), never sorts (negation rules depend on order).
merge_gitignore() {
  {
    cat .gitignore 2>/dev/null || true
    echo
    git show "$SRC_REF:.gitignore" 2>/dev/null || true
  } | awk '/^[[:space:]]*$/ || !seen[$0]++' | cat -s > .gitignore.tmp
  mv .gitignore.tmp .gitignore
}

# Mirror one directory exactly (adds, updates AND deletions) from a ref.
mirror_dir() {
  local ref="$1" dir="$2"
  git rm -r -q --ignore-unmatch -- "$dir"
  rm -rf -- "$dir"
  if git cat-file -e "$ref:$dir" 2>/dev/null; then
    git checkout "$ref" -- "$dir"
  fi
}

commit_push() {
  local branch="$1" msg="$2"
  if git diff --cached --quiet; then
    echo "No changes for $branch"
  else
    git commit -q -m "$msg"
    git push origin "HEAD:$branch"
    echo "Pushed $branch"
  fi
}

# ---- 1. ml/ + .gitignore -> every target branch -----------------------
for T in "${TARGETS[@]}"; do
  echo "---- $T"
  branch_exists "$T" || { echo "Skipping: $T not on origin"; continue; }

  git checkout -q -B "$T" "origin/$T"
  mirror_dir "$SRC_REF" "$SYNC_DIR"
  merge_gitignore
  git add -A -- "$SYNC_DIR" .gitignore      # nothing else is staged
  commit_push "$T" "$MSG_TAG: update $SYNC_DIR/ and merge .gitignore from main"
done

# ---- 2. devbridge/ : mob-dev -> mob-dev2 (only if mob-dev2 has no own changes)
if [[ -n "$BRIDGE_FROM" && -n "$BRIDGE_TO" ]] \
   && branch_exists "$BRIDGE_FROM" && branch_exists "$BRIDGE_TO"; then
  git fetch origin --prune
  # Commits on BRIDGE_TO (not in BRIDGE_FROM) touching devbridge/, ignoring our own sync commits
  OWN=$(git log --oneline "origin/$BRIDGE_FROM..origin/$BRIDGE_TO" \
          --grep="$MSG_TAG" --invert-grep -- "$BRIDGE_DIR")
  if [[ -z "$OWN" ]]; then
    echo "---- $BRIDGE_TO has no own $BRIDGE_DIR changes; mirroring from $BRIDGE_FROM"
    git checkout -q -B "$BRIDGE_TO" "origin/$BRIDGE_TO"
    mirror_dir "origin/$BRIDGE_FROM" "$BRIDGE_DIR"
    git add -A -- "$BRIDGE_DIR"
    commit_push "$BRIDGE_TO" "$MSG_TAG: mirror $BRIDGE_DIR/ from $BRIDGE_FROM"
  else
    echo "Skipping devbridge: $BRIDGE_TO has its own changes:"; echo "$OWN"
  fi
fi

echo "Done."
