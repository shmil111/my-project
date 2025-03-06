# PowerShell script to rename files with hyphens to PascalCase

function ConvertToPascalCase {
    param (
        [string]$fileName
    )
    
    # Remove file extension
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($fileName)
    $extension = [System.IO.Path]::GetExtension($fileName)
    
    # Split by hyphens and convert each part to title case
    $parts = $baseName -split '-'
    $pascalCaseParts = @()
    
    foreach ($part in $parts) {
        if ($part) {
            $pascalCaseParts += (Get-Culture).TextInfo.ToTitleCase($part.ToLower())
        }
    }
    
    # Join parts and add extension back
    $pascalCaseName = [string]::Join('', $pascalCaseParts) + $extension
    
    return $pascalCaseName
}

# Get all files with hyphens in their names
$filesToRename = Get-ChildItem -Path . -Recurse -File | 
                Where-Object { $_.Name -match '-' -and $_.Name -match '\.(ps1|js|py|sh|bat)$' -and -not $_.FullName.Contains('nodemodules') }

# Display files that will be renamed
Write-Host "Files to be renamed:"
foreach ($file in $filesToRename) {
    $newName = ConvertToPascalCase -fileName $file.Name
    Write-Host "  $($file.Name) -> $newName"
}

# Confirm before proceeding
$confirmation = Read-Host "Do you want to proceed with renaming these files? (y/n)"
if ($confirmation -ne 'y') {
    Write-Host "Operation cancelled."
    exit
}

# Rename files
foreach ($file in $filesToRename) {
    $newName = ConvertToPascalCase -fileName $file.Name
    $directory = $file.DirectoryName
    
    try {
        Rename-Item -Path $file.FullName -NewName $newName -ErrorAction Stop
        Write-Host "Renamed: $($file.Name) -> $newName" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to rename $($file.Name): $_" -ForegroundColor Red
    }
}

Write-Host "File renaming completed." -ForegroundColor Green 