# Registers the hourly job. Runs as you, only while you are logged in, with no window.
$root = $PSScriptRoot
$action = New-ScheduledTaskAction -Execute (Join-Path $root ".venv\Scripts\pythonw.exe") `
    -Argument "`"$(Join-Path $root 'fetch_news.py')`"" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Hours 1)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "RiyadhNewsDesk" -Action $action -Trigger $trigger -Settings $settings `
    -Description "Hourly Riyadh news collection and publish" -Force | Out-Null
Write-Host "Scheduled task 'RiyadhNewsDesk' registered (hourly)."
