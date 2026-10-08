# Prints each template .html in this folder to a letter-size .pdf next to it, using headless Chrome (or Edge).
# Run: powershell -ExecutionPolicy Bypass -File Assets\build-pdfs.ps1
# Then reload the CRM library from the new PDFs: see "Documents and Data Stack.md".

$ErrorActionPreference = 'Stop'

$browser = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $browser) { throw 'Chrome or Edge is needed to print the PDFs.' }

# a throwaway profile, so an open browser window doesn't interfere
$profileDir = Join-Path $env:TEMP 'intake-assets-pdf-profile'

foreach ($html in Get-ChildItem -Path $PSScriptRoot -Filter *.html) {
    $pdf = [IO.Path]::ChangeExtension($html.FullName, '.pdf')
    Remove-Item $pdf -ErrorAction SilentlyContinue
    $url = ([Uri]$html.FullName).AbsoluteUri
    Start-Process -FilePath $browser -Wait -WindowStyle Hidden -ArgumentList @(
        '--headless', '--disable-gpu', '--no-first-run', '--no-pdf-header-footer',
        "--user-data-dir=`"$profileDir`"", "--print-to-pdf=`"$pdf`"", $url
    )
    if (-not (Test-Path $pdf)) { throw "No PDF was written for $($html.Name)." }
    Write-Host "$($html.Name) -> $([IO.Path]::GetFileName($pdf))"
}
