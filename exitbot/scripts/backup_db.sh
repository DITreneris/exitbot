#!/bin/bash

# Database backup script for ExitBot
# Creates a timestamped backup of the PostgreSQL database

# Load environment variables
source ../.env

# Configuration
BACKUP_DIR="../backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/exitbot_db_${TIMESTAMP}.sql"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

echo "Starting database backup at ${TIMESTAMP}..."

# Extract database connection details from DATABASE_URL
if [[ -z "${DATABASE_URL}" ]]; then
    echo "Error: DATABASE_URL not set in .env file"
    exit 1
fi

# Parse DATABASE_URL
# Format: postgresql://user:password@host:port/dbname
DB_USER=$(echo $DATABASE_URL | sed -E 's/postgresql:\/\/([^:]+):.*/\1/')
DB_PASS=$(echo $DATABASE_URL | sed -E 's/postgresql:\/\/[^:]+:([^@]+).*/\1/')
DB_HOST=$(echo $DATABASE_URL | sed -E 's/postgresql:\/\/[^:]+:[^@]+@([^:]+).*/\1/')
DB_PORT=$(echo $DATABASE_URL | sed -E 's/postgresql:\/\/[^:]+:[^@]+@[^:]+:([^\/]+).*/\1/')
DB_NAME=$(echo $DATABASE_URL | sed -E 's/postgresql:\/\/[^:]+:[^@]+@[^:]+:[^\/]+\/([^?]+).*/\1/')

# Check if we're running inside Docker
if [ -f /.dockerenv ]; then
    # Inside Docker, use docker commands
    echo "Running inside Docker container, backing up from inside container..."
    docker exec -it exitbot_db pg_dump -U ${DB_USER} -h ${DB_HOST} -p ${DB_PORT} ${DB_NAME} > ${BACKUP_FILE}
else
    # Outside Docker, use local pg_dump
    echo "Running on host system, backing up using pg_dump..."
    PGPASSWORD=${DB_PASS} pg_dump -U ${DB_USER} -h ${DB_HOST} -p ${DB_PORT} ${DB_NAME} > ${BACKUP_FILE}
fi

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: ${BACKUP_FILE}"
    echo "Backup size: $(du -h ${BACKUP_FILE} | cut -f1)"
else
    echo "Backup failed!"
    exit 1
fi

# Compress the backup
gzip ${BACKUP_FILE}
echo "Backup compressed: ${BACKUP_FILE}.gz"

# List existing backups
echo "Existing backups:"
ls -lh ${BACKUP_DIR}

# Cleanup old backups (keep last 7)
find ${BACKUP_DIR} -name "*.sql.gz" -type f -mtime +7 -delete
echo "Cleaned up backups older than 7 days" 