# PowerShell script to schedule the API status dashboard update
# This script will create a scheduled task to run the update_dashboard.bat file

# Get the current directory where the script is located
$scriptPath = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$dashboardBatPath = Join-Path -Path $scriptPath -ChildPath "update_dashboard.bat"

# Task name and description
$taskName = "API_Status_Dashboard_Update"
$taskDescription = "Update the API Status Dashboard every hour to reflect current credential status"

# Check if the batch file exists
if (-not (Test-Path -Path $dashboardBatPath)) {
    Write-Error "Cannot find update_dashboard.bat at $dashboardBatPath"
    exit 1
}

# Create a new scheduled task action
$action = New-ScheduledTaskAction -Execute $dashboardBatPath -WorkingDirectory $scriptPath

# Create a trigger to run the task every hour
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)

# Create the task principal (who runs the task) - current user
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive

# Create the task settings
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries

# Register the scheduled task
try {
    # Check if the task already exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if ($existingTask) {
        # Task exists, update it
        Set-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description $taskDescription
        Write-Host "Updated existing scheduled task: $taskName"
    } else {
        # Task doesn't exist, create it
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description $taskDescription
        Write-Host "Created new scheduled task: $taskName"
    }
    
    Write-Host "The API Status Dashboard will be updated every hour."
    Write-Host "The next run time is: $($trigger.StartBoundary)"
    
} catch {
    Write-Error "Failed to create or update scheduled task: $_"
    exit 1
}

# Offer to run the update immediately
$runNow = Read-Host "Do you want to update the dashboard now? (y/n)"
if ($runNow -eq "y" -or $runNow -eq "Y") {
    Write-Host "Running update_dashboard.bat..."
    Start-Process -FilePath $dashboardBatPath -WorkingDirectory $scriptPath -Wait
    Write-Host "Update completed."
} 