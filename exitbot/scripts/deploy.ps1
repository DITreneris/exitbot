# ExitBot Deployment Script (PowerShell)
# This script automates the deployment process for the ExitBot application

param (
    [string]$Environment = "production"  # Default to production if not specified
)

# Configuration
$BackupDir = "..\backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ComposeFile = "..\docker-compose.prod.yml"
$MonitoringComposeFile = "..\docker-compose.monitoring.yml"
$EnvFile = "..\.env"
$BackupFile = "$BackupDir\exitbot_db_$Timestamp.sql"

# Function to display usage
function Show-Usage {
    Write-Host "Usage: .\deploy.ps1 [environment]"
    Write-Host "  environment: 'production' (default), 'staging', or 'development'"
    exit 1
}

# Function to display steps with colored output
function Write-Step {
    param ([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Blue
}

function Write-Success {
    param ([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Green
}

function Write-Error {
    param ([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Red
    exit 1
}

function Write-Warning {
    param ([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Yellow
}

# Check for valid environment
if ($Environment -ne "production" -and $Environment -ne "staging" -and $Environment -ne "development") {
    Write-Error "Invalid environment: $Environment"
    Show-Usage
}

# Display deployment banner
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    ExitBot Deployment - $Environment    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if docker is installed
Write-Step "Checking prerequisites..."
try {
    $null = & docker --version
} catch {
    Write-Error "Docker is not installed. Please install Docker before proceeding."
}

# Ensure environment file exists
Write-Step "Checking environment configuration..."
if (-not (Test-Path -Path $EnvFile)) {
    Write-Error "Environment file not found: $EnvFile"
}

# Update environment file for the selected environment
Write-Step "Configuring environment for $Environment..."
$EnvContent = Get-Content -Path $EnvFile
$EnvContent = $EnvContent -replace "^ENVIRONMENT=.*", "ENVIRONMENT=$Environment"
Set-Content -Path $EnvFile -Value $EnvContent

# Create backup directory if it doesn't exist
if (-not (Test-Path -Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

# Backup database if running in production
if ($Environment -eq "production") {
    Write-Step "Backing up production database..."
    $runningContainers = & docker-compose ps
    if ($runningContainers -match "exitbot_db") {
        try {
            & docker-compose exec -T db pg_dump -U postgres exitbot | Out-File -FilePath $BackupFile -Encoding utf8
            Write-Success "Database backup created: $BackupFile"
            Compress-Archive -Path $BackupFile -DestinationPath "$BackupFile.zip" -Force
            Remove-Item -Path $BackupFile
        } catch {
            Write-Warning "Database backup failed, proceeding anyway..."
        }
    } else {
        Write-Warning "Database container not running, skipping backup..."
    }
}

# Stop any running containers
Write-Step "Stopping existing containers..."
try {
    & docker-compose -f $ComposeFile down
} catch {
    Write-Warning "No containers to stop"
}

# Build images
Write-Step "Building Docker images..."
& docker-compose -f $ComposeFile build

# Start containers
Write-Step "Starting containers..."
& docker-compose -f $ComposeFile up -d

# Display status
Write-Step "Checking container status..."
& docker-compose -f $ComposeFile ps

# Wait for API to become available
Write-Step "Waiting for API to become available..."
$apiAvailable = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Success "API is up and running!"
            $apiAvailable = $true
            break
        }
    } catch {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
}

if (-not $apiAvailable) {
    Write-Warning "API did not become available in the expected time"
}

# Set up monitoring if in production
if ($Environment -eq "production") {
    Write-Step "Setting up monitoring..."
    if (Test-Path -Path $MonitoringComposeFile) {
        & docker-compose -f $MonitoringComposeFile up -d
        Write-Success "Monitoring services started"
    } else {
        Write-Warning "Monitoring configuration not found, skipping..."
    }
}

# Run database migrations
Write-Step "Running database migrations..."
try {
    & docker-compose -f $ComposeFile exec api python -m database.init_db
} catch {
    Write-Warning "Database migration failed"
}

# Display deployment info
Write-Success "Deployment completed successfully!"
Write-Host "`nExitBot is now available at:"
Write-Host "  API: http://localhost:8000"
Write-Host "  Frontend: http://localhost:3000"

if ($Environment -eq "production") {
    Write-Host "`nMonitoring is available at:"
    Write-Host "  Grafana: http://localhost:3001"
    Write-Host "  Prometheus: http://localhost:9090"
}

Write-Host "`nTo view logs:"
Write-Host "  docker-compose -f $ComposeFile logs -f"

Write-Host "`nDeployment completed on $(Get-Date)" 