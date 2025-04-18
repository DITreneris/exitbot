#!/bin/bash

# ExitBot Deployment Script
# This script automates the deployment process for the ExitBot application

set -e  # Exit on any error

# Configuration
ENVIRONMENT=${1:-production}  # Default to production if not specified
BACKUP_DIR="../backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
COMPOSE_FILE="../docker-compose.prod.yml"
MONITORING_COMPOSE_FILE="../docker-compose.monitoring.yml"
ENV_FILE="../.env"
BACKUP_FILE="${BACKUP_DIR}/exitbot_db_${TIMESTAMP}.sql"

# Function to display usage
usage() {
    echo "Usage: $0 [environment]"
    echo "  environment: 'production' (default), 'staging', or 'development'"
    exit 1
}

# Function to display steps with colored output
step() {
    echo -e "\e[1;34m==>\e[0m \e[1m$1\e[0m"
}

success() {
    echo -e "\e[1;32m==>\e[0m \e[1m$1\e[0m"
}

error() {
    echo -e "\e[1;31m==>\e[0m \e[1m$1\e[0m"
    exit 1
}

warning() {
    echo -e "\e[1;33m==>\e[0m \e[1m$1\e[0m"
}

# Check for valid environment
if [[ "$ENVIRONMENT" != "production" && "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "development" ]]; then
    error "Invalid environment: $ENVIRONMENT"
    usage
fi

# Display deployment banner
echo -e "\n\e[1;36m========================================\e[0m"
echo -e "\e[1;36m    ExitBot Deployment - $ENVIRONMENT    \e[0m"
echo -e "\e[1;36m========================================\e[0m\n"

# Check if docker and docker-compose are installed
step "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Please install Docker before proceeding."
fi

# Ensure environment file exists
step "Checking environment configuration..."
if [ ! -f "$ENV_FILE" ]; then
    error "Environment file not found: $ENV_FILE"
fi

# Update environment file for the selected environment
step "Configuring environment for $ENVIRONMENT..."
sed -i "s/^ENVIRONMENT=.*/ENVIRONMENT=$ENVIRONMENT/g" "$ENV_FILE"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup database if running in production
if [[ "$ENVIRONMENT" == "production" ]]; then
    step "Backing up production database..."
    if docker-compose ps | grep -q "exitbot_db"; then
        docker-compose exec -T db pg_dump -U postgres exitbot > "$BACKUP_FILE"
        if [ $? -eq 0 ]; then
            success "Database backup created: $BACKUP_FILE"
            gzip "$BACKUP_FILE"
        else
            warning "Database backup failed, proceeding anyway..."
        fi
    else
        warning "Database container not running, skipping backup..."
    fi
fi

# Stop any running containers
step "Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down || warning "No containers to stop"

# Build images
step "Building Docker images..."
docker-compose -f "$COMPOSE_FILE" build

# Start containers
step "Starting containers..."
docker-compose -f "$COMPOSE_FILE" up -d

# Display status
step "Checking container status..."
docker-compose -f "$COMPOSE_FILE" ps

# Wait for API to become available
step "Waiting for API to become available..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health &> /dev/null; then
        success "API is up and running!"
        break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 30 ]; then
        warning "API did not become available in the expected time"
    fi
done

# Set up monitoring if in production
if [[ "$ENVIRONMENT" == "production" ]]; then
    step "Setting up monitoring..."
    if [ -f "$MONITORING_COMPOSE_FILE" ]; then
        docker-compose -f "$MONITORING_COMPOSE_FILE" up -d
        success "Monitoring services started"
    else
        warning "Monitoring configuration not found, skipping..."
    fi
fi

# Run database migrations
step "Running database migrations..."
docker-compose -f "$COMPOSE_FILE" exec api python -m database.init_db || warning "Database migration failed"

# Display deployment info
success "Deployment completed successfully!"
echo -e "\nExitBot is now available at:"
echo -e "  API: http://localhost:8000"
echo -e "  Frontend: http://localhost:3000"

if [[ "$ENVIRONMENT" == "production" ]]; then
    echo -e "\nMonitoring is available at:"
    echo -e "  Grafana: http://localhost:3001"
    echo -e "  Prometheus: http://localhost:9090"
fi

echo -e "\nTo view logs:"
echo -e "  docker-compose -f $COMPOSE_FILE logs -f"

echo -e "\nDeployment completed on $(date)" 