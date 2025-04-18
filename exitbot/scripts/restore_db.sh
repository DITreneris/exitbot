#!/bin/bash

# Database restore script for ExitBot
# Restores a PostgreSQL database from a backup file

# Usage: ./restore_db.sh <backup_file>

# Load environment variables
source ../.env

# Check if backup file provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -lh ../backups
    exit 1
fi

BACKUP_FILE=$1

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file ${BACKUP_FILE} not found!"
    exit 1
fi

echo "Restoring database from ${BACKUP_FILE}..."

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

# Uncompress if compressed
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    echo "Uncompressing backup file..."
    gunzip -c "${BACKUP_FILE}" > /tmp/exitbot_restore.sql
    RESTORE_FILE="/tmp/exitbot_restore.sql"
else
    RESTORE_FILE="${BACKUP_FILE}"
fi

# Confirm before proceeding
echo "WARNING: This will overwrite the current database (${DB_NAME})"
read -p "Are you sure you want to proceed? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Check if we're running inside Docker
if [ -f /.dockerenv ]; then
    # Inside Docker, use docker commands
    echo "Running inside Docker container, restoring from inside container..."
    
    # Drop and recreate database
    docker exec -it exitbot_db psql -U ${DB_USER} -h ${DB_HOST} -p ${DB_PORT} -c "DROP DATABASE IF EXISTS ${DB_NAME};"
    docker exec -it exitbot_db psql -U ${DB_USER} -h ${DB_HOST} -p ${DB_PORT} -c "CREATE DATABASE ${DB_NAME};"
    
    # Restore from backup
    cat ${RESTORE_FILE} | docker exec -i exitbot_db psql -U ${DB_USER} -h ${DB_HOST} -p ${DB_PORT} ${DB_NAME}
else
    # Outside Docker, use local psql
    echo "Running on host system, restoring using psql..."
    
    # Drop and recreate database
    PGPASSWORD=${DB_PASS} psql -U ${DB_USER} -h ${DB_HOST} -p ${DB_PORT} -c "DROP DATABASE IF EXISTS ${DB_NAME};"
    PGPASSWORD=${DB_PASS} psql -U ${DB_USER} -h ${DB_HOST} -p ${DB_PORT} -c "CREATE DATABASE ${DB_NAME};"
    
    # Restore from backup
    PGPASSWORD=${DB_PASS} psql -U ${DB_USER} -h ${DB_HOST} -p ${DB_PORT} ${DB_NAME} < ${RESTORE_FILE}
fi

# Check if restore was successful
if [ $? -eq 0 ]; then
    echo "Restore completed successfully!"
else
    echo "Restore failed!"
    exit 1
fi

# Clean up temporary files
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    rm -f ${RESTORE_FILE}
fi 