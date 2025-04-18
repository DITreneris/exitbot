#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
python -m app.scripts.wait_for_db

# Run database migrations
echo "Running database migrations..."
python -m app.scripts.migrate_db

# Create initial admin user if not exists
echo "Ensuring admin user exists..."
python -m app.scripts.create_admin

# Start the application
echo "Starting ExitBot application..."
exec python -m app.main 