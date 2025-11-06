# Quick deployment setup for Windows
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Auto Form Filler - Deploy Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit - Auto Form Filler with ATS detection"
    git branch -M main
    Write-Host ""
    Write-Host "Git initialized!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Create a new repository on GitHub"
    Write-Host "2. Run: git remote add origin YOUR_GITHUB_URL"
    Write-Host "3. Run: git push -u origin main"
    Write-Host "4. Go to render.com and connect your repository"
} else {
    Write-Host "Git already initialized" -ForegroundColor Green
    Write-Host ""
    Write-Host "Checking for uncommitted changes..." -ForegroundColor Yellow
    $status = git status --porcelain
    if ($status) {
        Write-Host "Found uncommitted changes. Committing..." -ForegroundColor Yellow
        git add .
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        git commit -m "Update: $timestamp"
        Write-Host "Changes committed" -ForegroundColor Green
        Write-Host ""
        Write-Host "To deploy, run: git push" -ForegroundColor Yellow
    } else {
        Write-Host "No changes to commit" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Deployment Checklist:" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "[ ] Push code to GitHub"
Write-Host "[ ] Go to render.com"
Write-Host "[ ] Create new Web Service"
Write-Host "[ ] Connect GitHub repo"
Write-Host "[ ] Set build command: bash build.sh"
Write-Host "[ ] Set start command: cd backend && uvicorn main:app --host 0.0.0.0 --port `$PORT"
Write-Host "[ ] Deploy and wait ~5-10 minutes"
Write-Host ""
Write-Host "See DEPLOY-RENDER.md for detailed instructions" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Cyan
