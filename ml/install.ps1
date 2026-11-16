param (
    [Parameter(Mandatory=$false, Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$packages,

    [Alias("u")]
    [switch]$Uninstall,

    [switch]$Test
)

$PytestVersion="9.2.0"
$venv=Join-Path $PSScriptRoot "venv"
$python=Join-Path $venv "Scripts\python.exe"
$activate=Join-Path $venv "Scripts\Activate.ps1"
$reqPath=Join-Path $PSScriptRoot "requirements.txt"
$dotSourced=$MyInvocation.InvocationName -eq "."

function Stop-Install {
    param([string]$message)

    Write-Host $message -ForegroundColor Red

    # Exiting a dot-sourced script would close the terminal.
    if ($dotSourced) {
        throw $message
    }

    exit 1
}

function Invoke-Checked {
    param([string]$file, [string[]]$arguments)

    & $file @arguments

    if ($LASTEXITCODE -ne 0) {
        Stop-Install "Failed: $file $($arguments -join ' ')"
    }
}

if (Test-Path $python) {
    Write-Host "Using the existing virtual environment in $venv" -ForegroundColor Gray
} else {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Stop-Install "Python was not found. Install Python 3.12 or newer and try again."
    }

    Write-Host "Creating a virtual environment in $venv" -ForegroundColor Cyan
    Invoke-Checked "python" @("-m", "venv", $venv)
}

Invoke-Checked $python @("-m", "pip", "install", "--upgrade", "pip", "--quiet")

if ($packages.Count -gt 0) {
    $action=if ($Uninstall) { "uninstall" } else { "install" }
    $extra=if ($Uninstall) { @("-y") } else { @() }

    foreach ($package in $packages) {
        Write-Host "${action}: $package" -ForegroundColor Yellow
        Invoke-Checked $python (@("-m", "pip", $action, $package, "--quiet") + $extra)
    }

    Write-Host "Updating requirements.txt..." -ForegroundColor Cyan
    & $python -m pip freeze > $reqPath
    Write-Host "requirements.txt updated successfully!" -ForegroundColor Green

} elseif ($Uninstall) {
    Stop-Install "Provide package names to uninstall. Example: .\install.ps1 -u <package-name>"
} else {
    if (Test-Path $reqPath) {
        Write-Host "Installing dependencies from requirements.txt" -ForegroundColor Gray
        Invoke-Checked $python @("-m", "pip", "install", "-r", $reqPath, "--quiet")
    } else {
        Write-Host "requirements.txt not found at $reqPath. Skipping." -ForegroundColor Yellow
    }

    if ($Test) {
        Write-Host "Installing pytest $PytestVersion" -ForegroundColor Gray
        Invoke-Checked $python @("-m", "pip", "install", "pytest==$PytestVersion", "--quiet")
        & $python -m pip freeze > $reqPath
    }
}

if ($dotSourced) {
    . $activate
    Write-Host "Done. The virtual environment is active in this terminal." -ForegroundColor Green
} else {
    Write-Host "Done. Activate the virtual environment with:" -ForegroundColor Green
    Write-Host "    & `"$activate`""
}