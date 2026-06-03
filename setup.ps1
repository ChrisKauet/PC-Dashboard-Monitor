# PowerShell setup script for PC Dashboard Monitor
# Installs Python dependencies and prepares for executable creation

Write-Host "=== PC Dashboard Monitor Setup (PowerShell) ===" -ForegroundColor Cyan

# Check if Python is installed
Write-Host "Checking Python installation..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found in PATH. Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "Python version: $(python --version)" -ForegroundColor Green

# Upgrade pip
Write-Host "`nUpgrading pip..."
python -m pip install --upgrade pip

# Install dependencies from requirements.txt
if (Test-Path .\requirements.txt) {
    Write-Host "`nInstalling dependencies from requirements.txt..."
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Dependencies installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to install dependencies." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "requirements.txt not found!" -ForegroundColor Red
    exit 1
}

# Optional: Install PyInstaller for creating executables
Write-Host "`nWould you like to install PyInstaller to create a standalone executable? (y/n)"
$choice = Read-Host
if ($choice -ieq "y") {
    Write-Host "Installing PyInstaller..."
    python -m pip install pyinstaller
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PyInstaller installed successfully!" -ForegroundColor Green
        Write-Host "`nTo create an executable for this project, run:"
        Write-Host "  pyinstaller --onefile --windowed --add-data "".env;."" server.py"
        Write-Host ""
        Write-Host "Explanation of flags:")
        Write-Host "  --onefile      : Bundles everything into a single executable"
        Write-Host "  --windowed     : Prevents console window from showing (GUI app)"
        Write-Host "  --add-data     : Includes the .env file in the executable"
        Write-Host ""
        Write-Host "After building, the executable will be in the 'dist' folder.")
        Write-Host "You'll need to copy your .env file to the dist folder alongside the executable")
        Write-Host "for it to work correctly (since Supabase credentials are needed).")
        Write-Host ""
        Write-Host "To test the executable:")
        Write-Host "  .\dist\server.exe")
        Write-Host ""
        Write-Host "To install as a Windows service (using NSSM):")
        Write-Host "  1. Download NSSM from https://nssm.cc/download")
        Write-Host "  2. Run: nssm install PCSensorDash <path-to>\dist\server.exe")
        Write-Host "  3. Configure the service to start automatically")
    } else {
        Write-Host "Failed to install PyInstaller." -ForegroundColor Red
    }
} else {
    Write-Host "`nSkipping PyInstaller installation." -ForegroundColor Yellow
}

Write-Host "`nSetup complete!" -ForegroundColor Cyan
Write-Host "`nNext steps:"
Write-Host "1. Configure your .env file with Supabase credentials (SUPABASE_URL and SUPABASE_SERVICE_KEY)"
Write-Host "2. Run 'python server.py' to test the collector in development mode")
Write-Host "3. To create executable: Run this script again and choose 'y' for PyInstaller")
Write-Host "4. Install executable as Windows service using NSSM (see install_service.bat for guidance)")
EOF