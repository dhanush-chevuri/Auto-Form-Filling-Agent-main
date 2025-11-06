# Auto-install Tesseract OCR for Windows
Write-Host "=== Tesseract OCR Setup ===" -ForegroundColor Cyan
Write-Host ""

$tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"

# Check if already installed
if (Test-Path $tesseractPath) {
    Write-Host "✓ Tesseract OCR is already installed at: $tesseractPath" -ForegroundColor Green
    & $tesseractPath --version
    Write-Host ""
    Write-Host "Setup complete! Your backend is ready for OCR." -ForegroundColor Green
    exit 0
}

Write-Host "Tesseract OCR not found. Installing..." -ForegroundColor Yellow
Write-Host ""

# Download Tesseract installer
$installerUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
$installerPath = "$env:TEMP\tesseract-installer.exe"

Write-Host "Downloading Tesseract OCR installer..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "✓ Download complete" -ForegroundColor Green
} catch {
    Write-Host "✗ Download failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download manually from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Yellow
    exit 1
}

# Run installer
Write-Host ""
Write-Host "Running installer (this will open a window)..." -ForegroundColor Cyan
Write-Host "IMPORTANT: Accept the default installation path!" -ForegroundColor Yellow
Write-Host ""

Start-Process -FilePath $installerPath -Wait

# Verify installation
if (Test-Path $tesseractPath) {
    Write-Host ""
    Write-Host "✓ Tesseract OCR installed successfully!" -ForegroundColor Green
    & $tesseractPath --version
    Write-Host ""
    Write-Host "Setup complete! Restart your backend server." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Installation verification failed" -ForegroundColor Red
    Write-Host "Please check if Tesseract was installed correctly" -ForegroundColor Yellow
}

# Cleanup
Remove-Item $installerPath -ErrorAction SilentlyContinue
