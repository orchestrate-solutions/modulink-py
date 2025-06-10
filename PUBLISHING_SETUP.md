# GitHub Actions CI/CD Publishing Setup Guide

This guide will help you configure automated publishing to PyPI and TestPyPI using GitHub Actions with Trusted Publishing.

## 🚀 Overview

We've created a modern CI/CD pipeline that:
- **Builds** your package on every push
- **Tests** across multiple Python versions
- **Publishes to TestPyPI** on main branch pushes (for testing)
- **Publishes to PyPI** on tagged releases (for production)

## 🔧 Workflow Files

### 1. `publish-to-pypi.yml` - Main Publishing Workflow
- Builds distribution packages
- Publishes to TestPyPI on main branch pushes
- Publishes to PyPI on version tag pushes (`v*`)
- Uses Trusted Publishing (no API tokens needed!)

### 2. `python-publish.yml` - CI Testing Workflow  
- Runs tests across Python 3.9-3.13
- Performs linting and formatting checks
- Builds and verifies packages
- Runs on PRs and pushes to main/develop

## 🔐 Setting Up Trusted Publishing

### Step 1: Configure PyPI Trusted Publishers

1. **For PyPI** (production releases):
   - Go to https://pypi.org/manage/account/publishing/
   - Fill in:
     - **PyPI project name**: `modulink-py`
     - **Owner**: `JoshuaWink` (or your GitHub username)
     - **Repository name**: `modulink-py`
     - **Workflow filename**: `publish-to-pypi.yml`
     - **Environment name**: `pypi`
   - Click "Add"

2. **For TestPyPI** (test releases):
   - Go to https://test.pypi.org/manage/account/publishing/
   - Fill in the same information but:
     - **Environment name**: `testpypi`
   - Click "Add"

> **Note**: You need separate accounts for PyPI and TestPyPI. If you don't have a TestPyPI account, create one at https://test.pypi.org/account/register/

### Step 2: Configure GitHub Environments

1. Go to your GitHub repository: `https://github.com/JoshuaWink/modulink-py`
2. Click **Settings** → **Environments**
3. Create two environments:

#### Environment: `pypi`
- **Name**: `pypi`
- **Protection rules**: 
  - ✅ **Required reviewers** (add yourself)
  - ✅ **Restrict pushes to protected branches only**
- This ensures manual approval for production releases

#### Environment: `testpypi`  
- **Name**: `testpypi`
- **Protection rules**: None needed (auto-publishes on main)

## 🏷️ Publishing Releases

### Development Releases (TestPyPI)
Every push to the `main` branch automatically publishes to TestPyPI:
```bash
git push origin main
```

### Production Releases (PyPI)
Tag your releases to trigger PyPI publishing:

```bash
# Using your existing release script
python release.py patch   # 2.0.2 → 2.0.3
python release.py minor   # 2.0.2 → 2.1.0  
python release.py major   # 2.0.2 → 3.0.0

# Or manually
git tag v2.0.3
git push origin v2.0.3
```

## 🔄 Migration from Old Setup

### Remove Old API Tokens
If you had API tokens before, remove them:

1. **GitHub Secrets**: Go to Settings → Secrets → Actions
   - Delete `PYPI_API_TOKEN` (if exists)
   - Delete `TEST_PYPI_API_TOKEN` (if exists)

2. **PyPI Account**: Go to Account Settings → API tokens
   - Revoke any old tokens for this project

### Benefits of Trusted Publishing
- ✅ **More secure**: No long-lived API tokens
- ✅ **Automatic**: Tokens are generated per-release and expire immediately  
- ✅ **Simpler**: No secret management needed
- ✅ **Audit trail**: Better tracking of who published what

## 🧪 Testing the Setup

### Test TestPyPI Publishing
1. Make a small change to your code
2. Push to main: `git push origin main`
3. Check the Actions tab for the workflow run
4. Verify your package appears at: https://test.pypi.org/project/modulink-py/

### Test PyPI Publishing
1. Create and push a tag: 
   ```bash
   git tag v2.0.3-test
   git push origin v2.0.3-test
   ```
2. **IMPORTANT**: You'll need to manually approve the deployment in GitHub
3. Check that your package appears at: https://pypi.org/project/modulink-py/

## 🚨 Important Notes

### Version Management
- Your `setup.py` and `pyproject.toml` both contain version `2.0.2`
- Make sure to keep them in sync, or use a tool like `setuptools_scm`
- The `release.py` script updates `setup.py` but should also update `pyproject.toml`

### Environment Protection
- The `pypi` environment **requires manual approval** for security
- You'll get a notification when a tagged release needs approval
- The `testpypi` environment publishes automatically

### Package Names
- TestPyPI and PyPI use the same package name: `modulink-py`
- Make sure your TestPyPI versions don't conflict with production versions
- Consider using dev versions like `2.0.3.dev1` for TestPyPI

## 🔍 Troubleshooting

### Common Issues

1. **"Environment protection rules not configured"**
   - Create the `pypi` and `testpypi` environments in GitHub Settings

2. **"OIDC token not configured"**
   - Ensure Trusted Publishing is set up correctly on PyPI/TestPyPI
   - Check that environment names match exactly

3. **"Package already exists"**
   - You can't upload the same version twice
   - Bump your version using `python release.py patch`

4. **Workflow doesn't trigger**
   - Check that you're pushing tags, not just branches
   - Ensure tag format matches `v*` (e.g., `v2.0.3`)

### Getting Help
- Check the Actions tab for detailed error logs
- Review the [Python Packaging Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- File an issue in the repository if you encounter problems

## 🎉 You're All Set!

Once configured, your publishing workflow will be:

1. **Development**: Push to main → Auto-publish to TestPyPI
2. **Release**: Push a tag → Manual approval → Publish to PyPI
3. **Testing**: Install from TestPyPI to verify everything works
4. **Production**: Users install from PyPI

Happy publishing! 🚀
