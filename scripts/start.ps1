param(
    [switch]$Internet
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$LogPath = Join-Path $ProjectRoot "startup-error.log"

function Find-Python {
    $candidates = @(
        @{ File = "py.exe"; Prefix = @("-3") },
        @{ File = (Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"); Prefix = @() },
        @{ File = "python.exe"; Prefix = @() }
    )
    foreach ($candidate in $candidates) {
        try {
            $arguments = @($candidate.Prefix) + @("--version")
            $null = & $candidate.File @arguments 2>&1
            if ($LASTEXITCODE -eq 0) {
                return [pscustomobject]@{
                    File = $candidate.File
                    Prefix = @($candidate.Prefix)
                }
            }
        } catch {
            # Try the next Python installation.
        }
    }
    throw "No working Python 3 installation was found. Install Python from python.org and select Add Python to PATH."
}

function Find-OrInstall-Cloudflared {
    $ToolsDirectory = Join-Path $ProjectRoot "tools"
    $LocalExecutable = Join-Path $ToolsDirectory "cloudflared.exe"
    if (Test-Path -LiteralPath $LocalExecutable) {
        return $LocalExecutable
    }
    $installed = Get-Command cloudflared.exe -ErrorAction SilentlyContinue
    if ($installed) {
        return $installed.Source
    }
    Write-Host "First run: downloading Cloudflare Tunnel..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $ToolsDirectory -Force | Out-Null
    $temporary = "$LocalExecutable.download"
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $temporary
        if ((Get-Item -LiteralPath $temporary).Length -lt 1MB) {
            throw "Downloaded tunnel component is unexpectedly small."
        }
        Move-Item -LiteralPath $temporary -Destination $LocalExecutable -Force
    } finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
    return $LocalExecutable
}

try {
    if (Test-Path -LiteralPath $LogPath) {
        Remove-Item -LiteralPath $LogPath -Force
    }
    Write-Host "Starting Windows Web Remote..." -ForegroundColor Green
    $basePython = Find-Python
    $venvDirectory = Join-Path $ProjectRoot ".venv"
    $python = Join-Path $venvDirectory "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $python)) {
        Write-Host "Creating the project Python environment..."
        $arguments = @($basePython.Prefix) + @("-m", "venv", $venvDirectory)
        & $basePython.File @arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to create the project Python environment (exit code $LASTEXITCODE)."
        }
    }
    Write-Host "Checking dependencies..."
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed with exit code $LASTEXITCODE."
    }
    if ($Internet) {
        $cloudflared = Find-OrInstall-Cloudflared
        & $python server.py --internet --cloudflared $cloudflared
    } else {
        & $python server.py
    }
    if ($LASTEXITCODE -ne 0) {
        throw "The controller stopped with exit code $LASTEXITCODE."
    }
    exit 0
} catch {
    $details = @(
        "Time: $(Get-Date -Format o)"
        "Error: $($_.Exception.Message)"
        ""
        $_.ScriptStackTrace
    ) -join [Environment]::NewLine
    [IO.File]::WriteAllText($LogPath, $details, [Text.UTF8Encoding]::new($false))
    Write-Host ""
    Write-Host "Startup failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Error log: $LogPath" -ForegroundColor Yellow
    exit 1
}
