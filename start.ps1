<#
Start script for MultiFlow (Windows PowerShell)

Usage:
  .\start.ps1           # build client if needed, start server, open browser
  .\start.ps1 -Rebuild  # force rebuild of client before starting

This script will:
 - Build the frontend in client/vite -> output goes to client/web (if index.html missing or -Rebuild)
 - Start the Python server (server/server.py) in a new PowerShell window
 - Open http://localhost:5000 in the default browser
#>

param(
    [switch]$Rebuild
)

function Write-Info($msg){ Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Err($msg){ Write-Host "[ERROR] $msg" -ForegroundColor Red }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$clientWebIndex = Join-Path $scriptDir 'client\web\index.html'
$viteDir = Join-Path $scriptDir 'client\vite'

if ($Rebuild -or -not (Test-Path $clientWebIndex)) {
    Write-Info "Building frontend (client/vite)..."
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Write-Err "npm is not available in PATH. Install Node.js and npm to build the frontend."
        exit 1
    }

    # If node_modules missing, run npm install first
    $nodeModules = Join-Path $viteDir 'node_modules'
    if (-not (Test-Path $nodeModules)) {
        Write-Info "node_modules not found in client/vite. Running 'npm install'..."

        # Locate npm. On Windows npm is often a cmd shim (npm.cmd). Use Get-Command to find the executable.
        $npmCmd = (Get-Command npm -ErrorAction SilentlyContinue)
        if (-not $npmCmd) {
            Write-Err "npm is not available in PATH. Install Node.js and npm to build the frontend."
            exit 1
        }

        # If the resolved command is a file ending with .cmd or .exe, call it directly. Otherwise invoke via cmd.exe /c.
        $npmPath = $npmCmd.Source
        if ($npmPath -and ($npmPath -match '\.cmd$' -or $npmPath -match '\.exe$')) {
            $i = Start-Process -FilePath $npmPath -ArgumentList 'install' -WorkingDirectory $viteDir -NoNewWindow -Wait -PassThru
        } else {
            # Fallback: use cmd.exe /c npm install so shell script shims work correctly
            $i = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','npm install' -WorkingDirectory $viteDir -NoNewWindow -Wait -PassThru
        }

        if ($i.ExitCode -ne 0) { Write-Err "npm install failed (exit $($i.ExitCode))"; exit $i.ExitCode }
    }

    # Run the build script
    $npmCmd = (Get-Command npm -ErrorAction SilentlyContinue)
    $npmPath = $npmCmd.Source
    if ($npmPath -and ($npmPath -match '\.cmd$' -or $npmPath -match '\.exe$')) {
        $b = Start-Process -FilePath $npmPath -ArgumentList 'run','build' -WorkingDirectory $viteDir -NoNewWindow -Wait -PassThru
    } else {
        $b = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','npm run build' -WorkingDirectory $viteDir -NoNewWindow -Wait -PassThru
    }
    if ($b.ExitCode -ne 0) { Write-Err "Frontend build failed (exit $($b.ExitCode))"; exit $b.ExitCode }
    Write-Info "Frontend build finished."
} else {
    Write-Info "Frontend already built (client/web/index.html exists). Use -Rebuild to force a build."
}

# Start the Python server in a new PowerShell window so logs are visible
$serverFile = Join-Path $scriptDir 'server\server.py'
if (-not (Test-Path $serverFile)) {
    Write-Err "Server file not found: $serverFile"
    exit 1
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Err "python is not available in PATH. Install Python to run the server."
    exit 1
}

$serverDir = Join-Path $scriptDir 'server'
Write-Info "Starting server in a new PowerShell window (working dir: $serverDir)..."
Start-Process -FilePath powershell -ArgumentList '-NoExit','-Command',"cd `"$serverDir`"; python `"$serverFile`"" -WorkingDirectory $serverDir

Start-Sleep -Seconds 1
$clientDir = Join-Path $scriptDir 'client'
$clientFile = Join-Path $clientDir 'client.py'
if (Test-Path $clientFile) {
    Write-Info "Starting client in a new PowerShell window (working dir: $clientDir)..."
    Start-Process -FilePath powershell -ArgumentList '-NoExit','-Command',"cd `"$clientDir`"; python `"$clientFile`"" -WorkingDirectory $clientDir
    Write-Info "Started Python server and client. Server working directory: $serverDir, client working directory: $clientDir"
} else {
    Write-Info "Client file not found ($clientFile). Started server only."
}
