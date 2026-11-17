$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location (Join-Path $repoRoot "environments/local")
try {
    terraform destroy
}
finally {
    Pop-Location
}
