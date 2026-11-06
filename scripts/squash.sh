git checkout mob-dev2
git pull origin mob-dev2
git checkout --orphan temp-mob2-squash
git add -A
git commit -m "chore(mob-dev2): initial consolidated release synced from mob-dev"
git branch -D mob-dev2
git branch -m mob-dev2
git push origin mob-dev2 --force-with-lease