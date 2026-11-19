Set-Location "$PSScriptRoot\.."
New-Item -ItemType Directory -Force logs | Out-Null
& .\.venv\Scripts\python.exe -m quantagent.pipeline.run_daily *>> logs\daily.log
& .\.venv\Scripts\python.exe scripts\verify_ledger.py *>> logs\daily.log
