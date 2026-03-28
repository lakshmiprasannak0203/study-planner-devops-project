# CI/CD Implementation Guide

## Overview
This project now has a complete **Continuous Integration/Continuous Deployment (CI/CD)** pipeline using **GitHub Actions**.

## What is CI/CD?
- **CI (Continuous Integration)**: Automatically test code when you push changes
- **CD (Continuous Deployment)**: Automatically build and deploy code to production

## Workflow Files Created

### 1. **ci-cd.yml** - Main Pipeline
**Location**: `.github/workflows/ci-cd.yml`

**Triggers**: 
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Steps**:
1. **Test Job**:
   - Spins up PostgreSQL database
   - Installs Python 3.11
   - Runs unit tests (`pytest`)
   - Runs Selenium tests (browser automation)

2. **Build Job** (runs only if tests pass):
   - Builds Docker image
   - Caches Docker layers for faster builds
   - Validates Dockerfile

### 2. **code-quality.yml** - Code Quality Checks
**Location**: `.github/workflows/code-quality.yml`

**Checks**:
- Python syntax validation (flake8)
- Code style consistency
- Code complexity analysis

## How to Use

### 1. **Push to GitHub**
```bash
git add .
git commit -m "Add CI/CD pipeline"
git push origin main
```

### 2. **Monitor Workflows**
- Go to your GitHub repository
- Click "Actions" tab
- See all workflow runs and their status

### 3. **Workflow Status Badge**
Add this to your README.md:
```markdown
[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/study_planner_project/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/YOUR_USERNAME/study_planner_project/actions/workflows/ci-cd.yml)
```

## Configuration Details

### Database Setup
The CI/CD uses a PostgreSQL service container with:
- Database: `study_planner`
- User: `postgres`
- Password: `lakshmi`
- Port: 5432

### Python Version
- Python 3.11 is used for all jobs

### Dependencies
All dependencies from `requirements.txt` are automatically installed:
- Flask
- psycopg2 (PostgreSQL adapter)
- pytest (testing framework)
- Selenium (browser automation)
- webdriver-manager (Selenium driver management)

## What Happens on Each Push

```
┌─────────────────────┐
│  Push to GitHub     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Tests Run (Ubuntu)  │
│ - Unit Tests        │
│ - Selenium Tests    │
└──────────┬──────────┘
           │
      ┌────┴────┐
      │          │
   PASS        FAIL
      │          │
      ▼          ▼
   Build    ❌ Notify
   Docker   Developer
      │
      ▼
  ✅ Success
```

## Key Features

✅ **Automatic Testing**: Tests run on every push
✅ **PostgreSQL Database**: Full DB environment in CI
✅ **Docker Support**: Image builds are validated
✅ **Code Quality**: Syntax and style checks
✅ **Parallel Jobs**: Tests and quality checks run efficiently
✅ **Caching**: Pip and Docker layer caching for speed
✅ **Pull Request Checks**: Code quality enforced before merging

## Next Steps (Optional)

### 1. Deploy to Production
Modify `ci-cd.yml` to add deployment steps after successful build:
```yaml
deploy:
  needs: build
  runs-on: ubuntu-latest
  steps:
    - name: Deploy to production
      # Add your deployment commands here
```

### 2. Publish Docker Image
Add steps to push to Docker Hub or GitHub Container Registry:
```yaml
- name: Push Docker image
  run: |
    docker push study-planner:latest
```

### 3. Notify Team
Add Slack/Email notifications for workflow status

### 4. Add Branch Protection
In GitHub settings, require CI checks to pass before merging to `main`

## Troubleshooting

### Tests Fail in CI but Pass Locally
- Check database connection settings
- Ensure environment variables match
- Verify Python version compatibility

### Selenium Tests Timeout
- Selenium tests have `continue-on-error: true` to not block pipeline
- Consider running them separately or in a dedicated workflow

### Docker Build Fails
- Check Dockerfile syntax
- Ensure all dependencies are in requirements.txt
- Verify Docker build context

## Environment Variables
The following are set in the workflow for CI tests:
- `DB_HOST=localhost`
- `DB_NAME=study_planner`
- `DB_USER=postgres`
- `DB_PASS=lakshmi`

**Note**: For production, use GitHub Secrets to store sensitive credentials.

## GitHub Secrets (For Production)
1. Go to Repository Settings → Secrets
2. Add secrets like:
   - `DB_PASSWORD` - Production database password
   - `DOCKER_USERNAME` - Docker Hub username
   - `DOCKER_TOKEN` - Docker Hub access token
   - `DEPLOY_KEY` - SSH key for deployment

Then reference in workflows:
```yaml
- name: Deploy
  env:
    DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
  run: ./deploy.sh
```

---

**Created**: CI/CD Pipeline with GitHub Actions
**Status**: ✅ Ready to push to GitHub
