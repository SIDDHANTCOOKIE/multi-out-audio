python -m pip install -q -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) { exit 1 }
python -m PyInstaller --noconfirm --onefile --windowed --name MultiOutAudio run_gui.py
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "Built dist\MultiOutAudio.exe"
