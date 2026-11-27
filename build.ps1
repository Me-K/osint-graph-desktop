param(
    [switch]$SkipInstall,
    [switch]$SkipUiBuild,
    [switch]$NoArchive
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$desktopPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$desktopRoot = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') + '\'
$desktopFinal = Join-Path $PSScriptRoot 'dist\OSINTGraph'
$desktopStage = Join-Path $PSScriptRoot ('build\portable-' + [Guid]::NewGuid().ToString('N'))
$desktopPrevious = Join-Path $PSScriptRoot ('build\previous-portable-' + [Guid]::NewGuid().ToString('N'))
# All directory moves must remain inside this desktop workspace.
foreach ($desktopPath in @($desktopFinal, $desktopStage, $desktopPrevious)) {
    if (-not [IO.Path]::GetFullPath($desktopPath).StartsWith($desktopRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Chemin de construction hors du dossier desktop.'
    }
}
$desktopRunning = Get-Process -Name OSINTGraph,QtWebEngineProcess -ErrorAction SilentlyContinue |
    # Keep only processes launched from the portable directory that will be replaced.
    Where-Object { $_.Path -and $_.Path.StartsWith($desktopFinal + '\', [StringComparison]::OrdinalIgnoreCase) }
if ($desktopRunning) { throw 'Fermez OSINT Graph avant de reconstruire le programme portable.' }

# Stop the build with a named error if the preceding external command failed.
function Assert-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step a echoue (code $LASTEXITCODE)." }
}

if (-not $SkipInstall) {
    if (-not (Test-Path -LiteralPath $desktopPython)) {
        python -m venv .venv
        Assert-Exit 'Creation de l environnement Python'
    }
    & $desktopPython -m pip install -r requirements-lock.txt
    Assert-Exit 'Installation Python'
    Push-Location ui
    try {
        npm.cmd ci --no-audit --no-fund
        Assert-Exit 'Installation de l interface'
    } finally { Pop-Location }
}
if (-not (Test-Path -LiteralPath $desktopPython)) { throw 'Environnement absent : relancer sans -SkipInstall.' }
if (-not $SkipUiBuild) {
    Push-Location ui
    try {
        npm.cmd run build
        Assert-Exit 'Compilation de l interface'
    } finally { Pop-Location }
}
& $desktopPython self_check.py
Assert-Exit 'Tests fonctionnels'
& $desktopPython collect_licenses.py
Assert-Exit 'Collecte des licences'
& $desktopPython -m PyInstaller --noconfirm --distpath $desktopStage OSINTGraph.spec
Assert-Exit 'Fabrication du programme portable'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $desktopFinal) | Out-Null
if (Test-Path -LiteralPath $desktopFinal) {
    Move-Item -LiteralPath $desktopFinal -Destination $desktopPrevious
}
try {
    Move-Item -LiteralPath (Join-Path $desktopStage 'OSINTGraph') -Destination $desktopFinal
} catch {
    if (Test-Path -LiteralPath $desktopPrevious) { Move-Item -LiteralPath $desktopPrevious -Destination $desktopFinal }
    throw
}
Copy-Item -LiteralPath README.md,THIRD_PARTY.md,VALIDATION.md -Destination dist/OSINTGraph
Copy-Item -LiteralPath PORTABLE.txt -Destination dist/OSINTGraph/LIRE-MOI.txt
if (-not $NoArchive) {
    & $desktopPython -c "import hashlib,pathlib,shutil; p=pathlib.Path(shutil.make_archive('dist/OSINTGraph-Windows-x64', 'zip', 'dist', 'OSINTGraph')); p.with_suffix('.zip.sha256').write_text(hashlib.file_digest(p.open('rb'),'sha256').hexdigest()+'  '+p.name+'\n', encoding='ascii')"
    Assert-Exit 'Creation de l archive'
}
Write-Host 'Programme pret : dist\OSINTGraph\OSINTGraph.exe'
