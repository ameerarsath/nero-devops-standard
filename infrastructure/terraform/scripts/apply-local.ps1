$ErrorActionPreference = "Stop"

# Can be invoked from any working directory. Requires Docker Desktop and Terraform.
# Reuse an existing container named "floci" instead of trying to create a duplicate.
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot
try {
    $existingFloci = docker ps -a --filter "name=^/floci$" --format "{{.Names}}"
    if ($existingFloci) {
        $runningFloci = docker ps --filter "name=^/floci$" --format "{{.Names}}"
        if (-not $runningFloci) { docker start floci | Out-Null }
    }
    else {
        docker compose up -d
    }
    terraform fmt -recursive

    Push-Location (Join-Path $repoRoot "environments/local")
    try {
        terraform init
        terraform validate
        terraform plan
        terraform apply
    }
    finally {
        Pop-Location
    }
}
finally {
    Pop-Location
}
