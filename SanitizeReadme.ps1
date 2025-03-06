# PowerShell script to sanitize README.md by replacing sensitive information patterns

$readmePath = "README.md"
$content = Get-Content $readmePath -Raw

Write-Host "Sanitizing README.md file..."

# Replace sensitive patterns with placeholders
$patterns = @(
    # Password pattern
    @{
        Pattern = 'password\s*=\s*["'']?[^"''\s]+["'']?'
        Replacement = 'password="[REDACTED]"'
    },
    # API Key pattern
    @{
        Pattern = 'api[_\-]?key\s*=\s*["'']?[^"''\s]+["'']?'
        Replacement = 'api_key="[REDACTED]"'
    },
    # Token pattern
    @{
        Pattern = 'token\s*=\s*["'']?[^"''\s]+["'']?'
        Replacement = 'token="[REDACTED]"'
    },
    # Secret pattern
    @{
        Pattern = 'secret[_\-]?key\s*=\s*["'']?[^"''\s]+["'']?'
        Replacement = 'secret_key="[REDACTED]"'
    },
    # Credential examples
    @{
        Pattern = 'echo\s+["''].*password.*["'']\s+>'
        Replacement = 'echo "[REDACTED]" >'
    },
    @{
        Pattern = 'echo\s+["''].*api[_\-]?key.*["'']\s+>'
        Replacement = 'echo "[REDACTED]" >'
    },
    @{
        Pattern = 'echo\s+["''].*token.*["'']\s+>'
        Replacement = 'echo "[REDACTED]" >'
    }
)

# Apply all patterns
foreach ($pattern in $patterns) {
    $content = $content -replace $pattern.Pattern, $pattern.Replacement
}

# Save the sanitized content back to the file
Set-Content -Path $readmePath -Value $content

Write-Host "README.md sanitized successfully." 