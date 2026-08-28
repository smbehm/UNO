# One-time setup: creates C:\Users\YOU\pdf-to-mp3 and installs dependencies.
# Run in PowerShell: irm <setup-url> | iex   OR   .\setup.ps1

$ErrorActionPreference = "Stop"
$Root = Join-Path $env:USERPROFILE "pdf-to-mp3"
$Scripts = Join-Path $Root "scripts"
$Inbox = Join-Path $Root "inbox"
$Output = Join-Path $Root "output"
$RepoBase = "https://github.com/smbehm/UNO/raw/cursor/pdf-read-aloud-b33f/pdf-to-mp3"

Write-Host "Creating folders at $Root ..."
New-Item -ItemType Directory -Force -Path $Scripts, $Inbox, $Output | Out-Null

Write-Host "Downloading scripts ..."
Invoke-WebRequest "$RepoBase/read_aloud.py" -OutFile (Join-Path $Scripts "read_aloud.py")
Invoke-WebRequest "$RepoBase/requirements.txt" -OutFile (Join-Path $Scripts "requirements.txt")
Invoke-WebRequest "$RepoBase/convert.ps1" -OutFile (Join-Path $Root "convert.ps1")

function Find-Python {
    $candidates = @(
        { & py -3.12 -c "import sys; print(sys.executable)" 2>$null },
        { & py -3.11 -c "import sys; print(sys.executable)" 2>$null },
        { & py -3 -c "import sys; print(sys.executable)" 2>$null },
        { & python -c "import sys; print(sys.executable)" 2>$null }
    )
    foreach ($fn in $candidates) {
        try {
            $exe = & $fn
            if ($exe -and (Test-Path $exe)) { return $exe.Trim() }
        } catch {}
    }
    return $null
}

$Python = Find-Python
if (-not $Python) {
    Write-Host ""
    Write-Host "Python 3.11 or 3.12 not found." -ForegroundColor Red
    Write-Host "Install with:  winget install Python.Python.3.12"
    Write-Host "Then close PowerShell, reopen, and run this setup again."
    exit 1
}

Write-Host "Using Python: $Python"
$Python | Out-File -FilePath (Join-Path $Root "python.txt") -Encoding ascii -NoNewline

Write-Host "Installing Python packages (first time may take a few minutes) ..."
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $Scripts "requirements.txt") `
    --extra-index-url https://download.pytorch.org/whl/cpu

Write-Host ""
Write-Host "Checking ffmpeg and espeak-ng ..."
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
$espeak = Get-Command espeak-ng -ErrorAction SilentlyContinue
if (-not $ffmpeg) {
    Write-Host "  ffmpeg missing — install:  winget install Gyan.FFmpeg" -ForegroundColor Yellow
}
if (-not $espeak) {
    Write-Host "  espeak-ng missing — install:  winget install espeak-ng.espeak-ng" -ForegroundColor Yellow
    Write-Host "  (Required for natural speech. Restart PowerShell after installing.)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Drop PDFs here:  $Inbox"
Write-Host "  MP3s appear in:  $Output"
Write-Host ""
Write-Host "Convert everything in inbox:"
Write-Host "  & `"$Root\convert.ps1`""
Write-Host ""
Write-Host "Convert one file (your Omniscience script):"
Write-Host "  & `"$Root\convert.ps1`" `"S:\Shared drives\SOURCE SCULPTURES\Omniscience\Omniscience_Final_2024.pdf`""
