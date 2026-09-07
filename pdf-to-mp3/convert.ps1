param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PdfPaths
)

$ErrorActionPreference = "Stop"
$Root = Join-Path $env:USERPROFILE "pdf-to-mp3"
$Scripts = Join-Path $Root "scripts"
$Inbox = Join-Path $Root "inbox"
$Output = Join-Path $Root "output"
$Voice = "am_michael"
$Speed = "0.95"

$PythonFile = Join-Path $Root "python.txt"
if (-not (Test-Path $PythonFile)) {
    Write-Host "Run setup first:  irm https://raw.githubusercontent.com/smbehm/UNO/cursor/pdf-read-aloud-b33f/pdf-to-mp3/setup.ps1 | iex"
    exit 1
}
$Python = Get-Content $PythonFile -Raw
$Script = Join-Path $Scripts "read_aloud.py"

if (-not (Test-Path $Script)) {
    Write-Host "Missing read_aloud.py — re-run setup.ps1"
    exit 1
}

New-Item -ItemType Directory -Force -Path $Output | Out-Null

function Convert-OnePdf {
    param([string]$Pdf)
    if (-not (Test-Path $Pdf)) {
        Write-Host "File not found: $Pdf" -ForegroundColor Red
        return
    }
    $name = [System.IO.Path]::GetFileNameWithoutExtension($Pdf)
    $mp3 = Join-Path $Output "$name.mp3"
    $txt = Join-Path $Output "$name.txt"
    Write-Host ""
    Write-Host "Converting: $Pdf" -ForegroundColor Cyan
    & $Python $Script $Pdf `
        -o $mp3 `
        --text-out $txt `
        --voice $Voice `
        --speed $Speed
    Write-Host "Saved: $mp3" -ForegroundColor Green
}

if ($PdfPaths -and $PdfPaths.Count -gt 0) {
    foreach ($p in $PdfPaths) {
        Convert-OnePdf $p
    }
} else {
    $pdfs = Get-ChildItem -Path $Inbox -Filter "*.pdf" -ErrorAction SilentlyContinue
    if (-not $pdfs -or $pdfs.Count -eq 0) {
        Write-Host "No PDFs in inbox: $Inbox"
        Write-Host ""
        Write-Host "Either copy a PDF into inbox, or pass a path:"
        Write-Host "  & `"$Root\convert.ps1`" `"C:\path\to\file.pdf`""
        exit 0
    }
    foreach ($f in $pdfs) {
        Convert-OnePdf $f.FullName
    }
}

Write-Host ""
Write-Host "Output folder: $Output"
