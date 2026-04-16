# Development Guidelines

## Git Workflow

```bash
# 1. Sync main
git switch main && git fetch && git pull

# 2. Branch
git checkout -b feature/your-feature-name
# prefix: feature/, fix/, refactor/

# 3. Commit often
git add <files>
git commit -m "Short description of what changed"

# 4. Test before pushing
docker compose exec server python manage.py test

# 5. Push
git push -u origin feature/your-feature-name
```

Open a PR to `main` on GitHub. Wait for CI to pass, then merge.

```bash
# 6. Clean up after merge
git switch main && git fetch && git pull
git branch -d feature/your-feature-name
```
