# Database backup script for ExitBot (PowerShell version)
# Creates a timestamped backup of the PostgreSQL database

# Configuration
$BackupDir = "..\backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$BackupDir\exitbot_db_$Timestamp.sql"

# Create backup directory if it doesn't exist
if (-not (Test-Path -Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

Write-Host "Starting database backup at $Timestamp..."

# Load environment variables from .env file
$EnvFile = "..\..\.env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $value = $Matches[2].Trim()
            Set-Item -Path "Env:$key" -Value $value
        }
    }
} else {
    Write-Host "Error: .env file not found!" -ForegroundColor Red
    exit 1
}

# Extract database connection details from DATABASE_URL
if ([string]::IsNullOrEmpty($env:DATABASE_URL)) {
    Write-Host "Error: DATABASE_URL not set in .env file" -ForegroundColor Red
    exit 1
}

# Parse DATABASE_URL
# Format: postgresql://user:password@host:port/dbname
$DatabaseUrl = $env:DATABASE_URL
$pattern = 'postgresql:\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/([^?]+)'
if ($DatabaseUrl -match $pattern) {
    $DbUser = $Matches[1]
    $DbPass = $Matches[2]
    $DbHost = $Matches[3]
    $DbPort = $Matches[4]
    $DbName = $Matches[5]
} else {
    Write-Host "Error: Could not parse DATABASE_URL" -ForegroundColor Red
    exit 1
}

# Check if pg_dump is available
$pgDumpPath = "pg_dump"
try {
    $null = & $pgDumpPath --version
} catch {
    Write-Host "Error: pg_dump not found! Make sure PostgreSQL is installed and in your PATH." -ForegroundColor Red
    exit 1
}

# Create backup
Write-Host "Running on host system, backing up using pg_dump..."
$env:PGPASSWORD = $DbPass
try {
    & $pgDumpPath -U $DbUser -h $DbHost -p $DbPort $DbName | Out-File -FilePath $BackupFile -Encoding utf8
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Backup completed successfully: $BackupFile" -ForegroundColor Green
        $fileInfo = Get-Item $BackupFile
        Write-Host "Backup size: $([Math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor Green
    } else {
        Write-Host "Backup failed!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error during backup: $_" -ForegroundColor Red
    exit 1
}

# Compress the backup
Write-Host "Compressing backup..."
try {
    Compress-Archive -Path $BackupFile -DestinationPath "$BackupFile.zip" -Force
    Write-Host "Backup compressed: $BackupFile.zip" -ForegroundColor Green
    # Remove original file after compression
    Remove-Item -Path $BackupFile
} catch {
    Write-Host "Error compressing backup: $_" -ForegroundColor Red
}

# List existing backups
Write-Host "Existing backups:" -ForegroundColor Yellow
Get-ChildItem -Path $BackupDir -Filter "*.zip" | Format-Table Name, LastWriteTime, @{Name="Size(MB)"; Expression={"{0:N2}" -f ($_.Length / 1MB)}}

# Cleanup old backups (keep last 7 days)
$oldBackups = Get-ChildItem -Path $BackupDir -Filter "*.zip" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
if ($oldBackups.Count -gt 0) {
    Write-Host "Cleaning up $($oldBackups.Count) backups older than 7 days..." -ForegroundColor Yellow
    $oldBackups | ForEach-Object { Remove-Item -Path $_.FullName -Force }
    Write-Host "Cleanup complete" -ForegroundColor Green
} 