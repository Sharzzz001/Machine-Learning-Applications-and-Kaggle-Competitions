cmd.exe /k ""Z:\Shared_Drive\MyTool\venv\Scripts\python.exe" "Z:\Shared_Drive\MyTool\my_script.py""

cmd.exe /c ""Z:\Corporate Folder\My Tool\venv\Scripts\python.exe" "Z:\Corporate Folder\My Tool\my_script.py""

# Get the folder where THIS script is saved (no matter how long the path is)
$currentDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Define paths to your venv and script
$pythonExe = Join-Path $currentDir "venv\Scripts\python.exe"
$myScript = Join-Path $currentDir "my_script.py"

# Check if the venv exists (for troubleshooting)
if (-not (Test-Path $pythonExe)) {
    Write-Host "Error: Virtual Environment not found at $pythonExe" -ForegroundColor Red
    pause
    exit
}

# Run the python script using the venv's python
& $pythonExe $myScript

# Optional: Keep window open if there's an error
if ($LASTEXITCODE -ne 0) {
    Write-Host "Script failed with exit code $LASTEXITCODE" -ForegroundColor Yellow
    pause
}
