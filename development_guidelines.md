# Development Guidelines

## Git Workflow

### 1. Stay Up to Date

Before starting any work, make sure your local `main` branch is up to date:

```bash
git switch main
git fetch
git pull 
```

### 2. Create a Feature Branch

Create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/add-user-auth` - for new features
- `fix/login-bug` - for bug fixes
- `refactor/cleanup-models` - for refactoring

### 3. Develop

Make your changes and commit frequently with clear messages:

```bash
git add .
git commit -m "Add user registration endpoint"
```

### 4. Run Tests

Before pushing, run the unit tests to make sure nothing is broken:

```bash
# Django tests
docker compose exec server python manage.py test

# Or locally
cd server
python manage.py test
```

### 5. Push Your Branch

```bash
git push -u origin feature/your-feature-name
```

### 6. Create a Pull Request

1. Go to GitHub and create a Pull Request from your branch to `main`
2. Add a clear description of your changes
3. Request a review if needed
4. Wait for CI checks to pass
5. Merge after approval

### 7. Clean Up

After your PR is merged, delete your local branch:

```bash
git switch main
git fetch
git pull 
git branch -d feature/your-feature-name
```
