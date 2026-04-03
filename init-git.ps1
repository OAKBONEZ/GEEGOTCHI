# PowerShell script to initialize git repository and commit all files
# Run this after system restart when bash fork issue is resolved

param(
    [string]$RemoteUrl = "",
    [string]$BranchName = "main"
)

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  Fancygotchi Git Initialization Script" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "✓ Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Git not found. Please install Git for Windows." -ForegroundColor Red
    exit 1
}

# Navigate to project directory
cd $projectDir
Write-Host "✓ Working directory: $projectDir" -ForegroundColor Green
Write-Host ""

# Initialize repository
Write-Host "Initializing git repository..." -ForegroundColor Yellow
git init
git config user.name "Fancygotchi Setup"
git config user.email "setup@fancygotchi.local"
Write-Host "✓ Git repository initialized" -ForegroundColor Green
Write-Host ""

# Add all files
Write-Host "Adding files to staging area..." -ForegroundColor Yellow
git add .
$fileCount = (git ls-files).Count
Write-Host "✓ Added $fileCount files" -ForegroundColor Green
Write-Host ""

# Create initial commit
Write-Host "Creating initial commit..." -ForegroundColor Yellow
git commit -m "Initial commit: Fancygotchi setup files and documentation with SSID whitelist"
Write-Host "✓ Initial commit created" -ForegroundColor Green
Write-Host ""

# Display current status
git status
Write-Host ""

# Setup remote if provided
if ($RemoteUrl -ne "") {
    Write-Host "Setting up remote repository..." -ForegroundColor Yellow
    git remote add origin $RemoteUrl
    Write-Host "✓ Remote configured: $RemoteUrl" -ForegroundColor Green
    Write-Host ""
    Write-Host "To push to remote, run:" -ForegroundColor Cyan
    Write-Host "  git push -u origin $BranchName" -ForegroundColor White
} else {
    Write-Host "No remote URL provided." -ForegroundColor Yellow
    Write-Host "To add a remote later:" -ForegroundColor Cyan
    Write-Host "  git remote add origin <repository-url>" -ForegroundColor White
    Write-Host "  git push -u origin $BranchName" -ForegroundColor White
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  Git initialization complete!" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
