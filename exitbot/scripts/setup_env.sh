#!/bin/bash
set -e

# Setup script for ExitBot deployment

# Display help message
show_help() {
    echo "ExitBot Setup Script"
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -p, --prod       Set up production environment"
    echo "  -d, --dev        Set up development environment (default)"
    echo "  -g, --groq       Use Groq as LLM provider"
    echo "  -o, --ollama     Use Ollama as LLM provider"
    echo ""
}

# Parse arguments
ENVIRONMENT="development"
LLM_PROVIDER="groq"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--prod)
            ENVIRONMENT="production"
            shift
            ;;
        -d|--dev)
            ENVIRONMENT="development"
            shift
            ;;
        -g|--groq)
            LLM_PROVIDER="groq"
            shift
            ;;
        -o|--ollama)
            LLM_PROVIDER="ollama"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Create .env file from template if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    # Update the secret key in .env
    sed -i "s/SECRET_KEY=change_this_to_a_secure_random_string/SECRET_KEY=$SECRET_KEY/" .env
    echo "Updated SECRET_KEY in .env"
else
    echo ".env file already exists. Skipping..."
fi

# Update environment-specific settings
sed -i "s/ENVIRONMENT=.*/ENVIRONMENT=$ENVIRONMENT/" .env
sed -i "s/LLM_PROVIDER=.*/LLM_PROVIDER=$LLM_PROVIDER/" .env

# Print environment info
echo "Environment: $ENVIRONMENT"
echo "LLM Provider: $LLM_PROVIDER"

# Create required directories
mkdir -p nginx/ssl
mkdir -p nginx/conf.d
mkdir -p logs

# Generate self-signed SSL certificates for development
if [ "$ENVIRONMENT" = "development" ]; then
    if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/key.pem ]; then
        echo "Generating self-signed SSL certificates for development..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        echo "SSL certificates generated."
    else
        echo "SSL certificates already exist. Skipping..."
    fi
else
    echo "For production, please provide your own SSL certificates."
    echo "Place them in nginx/ssl/cert.pem and nginx/ssl/key.pem"
fi

echo "Environment setup complete!"
echo "To start the application in $ENVIRONMENT mode, run:"
if [ "$ENVIRONMENT" = "production" ]; then
    echo "  docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
else
    echo "  docker-compose up -d" 