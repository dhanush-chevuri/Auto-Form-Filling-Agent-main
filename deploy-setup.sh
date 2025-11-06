#!/bin/bash
# Quick deployment script

echo "================================"
echo "Auto Form Filler - Deploy Setup"
echo "================================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - Auto Form Filler with ATS detection"
    git branch -M main
    echo ""
    echo "✓ Git initialized!"
    echo ""
    echo "Next steps:"
    echo "1. Create a new repository on GitHub"
    echo "2. Run: git remote add origin YOUR_GITHUB_URL"
    echo "3. Run: git push -u origin main"
    echo "4. Go to render.com and connect your repository"
else
    echo "✓ Git already initialized"
    echo ""
    echo "Checking for uncommitted changes..."
    if [[ -n $(git status -s) ]]; then
        echo "Found uncommitted changes. Committing..."
        git add .
        git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "✓ Changes committed"
        echo ""
        echo "To deploy, run: git push"
    else
        echo "✓ No changes to commit"
    fi
fi

echo ""
echo "================================"
echo "Deployment Checklist:"
echo "================================"
echo "[ ] Push code to GitHub"
echo "[ ] Go to render.com"
echo "[ ] Create new Web Service"
echo "[ ] Connect GitHub repo"
echo "[ ] Set build command: bash build.sh"
echo "[ ] Set start command: cd backend && uvicorn main:app --host 0.0.0.0 --port \$PORT"
echo "[ ] Deploy and wait ~5-10 minutes"
echo ""
echo "See DEPLOY-RENDER.md for detailed instructions"
echo "================================"
