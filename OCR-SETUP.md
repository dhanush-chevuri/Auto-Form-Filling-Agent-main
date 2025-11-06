# OCR Support Setup Guide

Your app now has OCR support to read scanned/image-based PDFs!

## Quick Setup (5 minutes)

### Step 1: Install Tesseract OCR

**Download and install Tesseract OCR:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Or direct link: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe
2. Run the installer
3. **IMPORTANT:** Use the default installation path: `C:\Program Files\Tesseract-OCR`
4. Click through the installation (accept all defaults)

### Step 2: Restart Backend

After installing Tesseract, restart your backend server:
```powershell
# Kill existing backend
$p = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess | Where-Object {$_ -ne 0 -and $_ -ne 4}
if ($p) { Stop-Process -Id $p -Force }

# Start backend in new window
cd "C:\Users\venki\OneDrive\Desktop\ROUTER\automatic-job-application-filler"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'backend'; & '.\venv\Scripts\python.exe' -m uvicorn main:app --host 0.0.0.0 --port 8000"
```

### Step 3: Test It!

Upload your PDF again - the backend will now:
1. Try standard text extraction first (fast)
2. If that fails, automatically use OCR (slower but works on scanned PDFs)

## How It Works

- **Text-based PDFs**: Extracted instantly (< 1 second)
- **Image/Scanned PDFs**: Uses OCR (5-15 seconds depending on pages)
- The backend logs will show "OCR successful" when OCR is used

## Troubleshooting

If you get "OCR libraries not available":
- Make sure you installed Tesseract to the default path
- Restart the backend server
- Check `C:\Program Files\Tesseract-OCR\tesseract.exe` exists

## Alternative: Use DOCX Format

If you don't want to install Tesseract, just use DOCX files instead of PDFs:
- Export your resume as `.docx` format
- Upload the DOCX file - it will work immediately with no OCR needed!
