param(
    [switch]$Internet
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ToolsDirectory = Join-Path $ProjectRoot "tools"
$LogPath = Join-Path $ProjectRoot "startup-error.log"
Set-Location -LiteralPath $ProjectRoot

function Install-PortablePython {
    $runtimeDirectory = Join-Path $ToolsDirectory "python"
    $python = Join-Path $runtimeDirectory "python.exe"
    if (Test-Path -LiteralPath $python) {
        return [pscustomobject]@{ File = $python; Prefix = @(); Portable = $true }
    }

    Write-Host "Python was not found. Downloading a private portable runtime..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $ToolsDirectory -Force | Out-Null
    New-Item -ItemType Directory -Path $runtimeDirectory -Force | Out-Null
    $archive = Join-Path $ToolsDirectory "python-runtime.zip"
    $getPip = Join-Path $ToolsDirectory "get-pip.py"
    $pythonUrl = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"
    $pipUrl = "https://bootstrap.pypa.io/get-pip.py"
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $pythonUrl -OutFile $archive
        if ((Get-Item -LiteralPath $archive).Length -lt 5MB) {
            throw "Downloaded Python archive is unexpectedly small."
        }
        Expand-Archive -LiteralPath $archive -DestinationPath $runtimeDirectory -Force
        $pathFile = Get-ChildItem -LiteralPath $runtimeDirectory -Filter "python*._pth" | Select-Object -First 1
        if (-not $pathFile) {
            throw "Portable Python path configuration was not found."
        }
        $pathConfiguration = [IO.File]::ReadAllText($pathFile.FullName)
        $pathConfiguration = $pathConfiguration.Replace("#import site", "import site")
        [IO.File]::WriteAllText($pathFile.FullName, $pathConfiguration, [Text.Encoding]::ASCII)
        New-Item -ItemType Directory -Path (Join-Path $runtimeDirectory "Lib\site-packages") -Force | Out-Null

        Invoke-WebRequest -UseBasicParsing -Uri $pipUrl -OutFile $getPip
        & $python $getPip --disable-pip-version-check
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to install pip into portable Python (exit code $LASTEXITCODE)."
        }
    } finally {
        Remove-Item -LiteralPath $archive, $getPip -Force -ErrorAction SilentlyContinue
    }
    return [pscustomobject]@{ File = $python; Prefix = @(); Portable = $true }
}

function Find-OrInstall-Python {
    $candidates = @(
        @{ File = "py.exe"; Prefix = @("-3") },
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
                    Portable = $false
                }
            }
        } catch {
            # Try the next installation.
        }
    }
    return Install-PortablePython
}

function Find-OrInstall-Cloudflared {
    $localExecutable = Join-Path $ToolsDirectory "cloudflared.exe"
    if (Test-Path -LiteralPath $localExecutable) {
        return $localExecutable
    }
    $installed = Get-Command cloudflared.exe -ErrorAction SilentlyContinue
    if ($installed) {
        return $installed.Source
    }

    Write-Host "Downloading Cloudflare Tunnel..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $ToolsDirectory -Force | Out-Null
    $temporary = "$localExecutable.download"
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $temporary
        if ((Get-Item -LiteralPath $temporary).Length -lt 1MB) {
            throw "Downloaded tunnel component is unexpectedly small."
        }
        Move-Item -LiteralPath $temporary -Destination $localExecutable -Force
    } finally {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
    }
    return $localExecutable
}

try {
    Remove-Item -LiteralPath $LogPath -Force -ErrorAction SilentlyContinue
    Write-Host "Starting Windows Web Remote..." -ForegroundColor Green

    $venvDirectory = Join-Path $ProjectRoot ".venv"
    $venvPython = Join-Path $venvDirectory "Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython) {
        $python = $venvPython
    } else {
        $basePython = Find-OrInstall-Python
        if ($basePython.Portable) {
            $python = $basePython.File
        } else {
            Write-Host "Creating the project Python environment..."
            $arguments = @($basePython.Prefix) + @("-m", "venv", $venvDirectory)
            & $basePython.File @arguments
            if ($LASTEXITCODE -ne 0) {
                throw "Unable to create the project Python environment (exit code $LASTEXITCODE)."
            }
            $python = $venvPython
        }
    }

    Write-Host "Checking dependencies..."
    & $python -m pip install --disable-pip-version-check -r requirements.txt
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
