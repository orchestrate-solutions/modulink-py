#!/bin/bash

# GitHub Actions CI/CD Test Script
# This script simulates what the GitHub Actions workflow will do

echo "🚀 Testing GitHub Actions CI/CD workflow locally..."

# Activate virtual environment
source venv/bin/activate

echo "📦 Step 1: Building distribution packages..."
python -m build
if [ $? -eq 0 ]; then
    echo "✅ Build successful"
else
    echo "❌ Build failed"
    exit 1
fi

echo "🔍 Step 2: Verifying packages with twine..."
twine check dist/*
if [ $? -eq 0 ]; then
    echo "✅ Package verification successful"
else
    echo "❌ Package verification failed"
    exit 1
fi

echo "🧪 Step 3: Running tests..."
python -m pytest tests/ -v
if [ $? -eq 0 ]; then
    echo "✅ Tests passed"
else
    echo "❌ Tests failed"
    exit 1
fi

echo "🎉 All checks passed! Your GitHub Actions workflow should work correctly."
echo ""
echo "📋 Next steps:"
echo "1. Configure Trusted Publishing on PyPI and TestPyPI"
echo "2. Set up GitHub Environments (pypi and testpypi)"
echo "3. Push to main branch to test TestPyPI publishing"
echo "4. Create a tag to test PyPI publishing"
echo ""
echo "📚 See PUBLISHING_SETUP.md for detailed instructions"
