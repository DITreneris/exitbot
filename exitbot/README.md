# ExitBot - AI-Powered Exit Interview Assistant

ExitBot is an AI-powered application designed to conduct automated exit interviews for employees leaving an organization. It uses large language models (LLMs) to provide a natural, conversational experience while collecting valuable insights for HR departments.

## Features

- **Automated Interviews**: Conduct exit interviews without human intervention
- **Natural Conversation**: LLM-powered responses provide a human-like experience
- **Flexible Deployment**: Run with cloud-based (Groq) or local (Ollama) LLMs
- **Interactive Dashboard**: HR admins can view and analyze interview results
- **Customizable Workflows**: Configure interview questions and process
- **Comprehensive Reporting**: Generate summary reports with key insights
- **Secure Authentication**: Role-based access control with JWT tokens
- **REST API**: Well-documented API for potential integrations
- **Support for both Groq and Ollama as LLM providers**
- **API for frontend integration**
- **Reporting and analytics**
- **Authentication and authorization**
- **PostgreSQL database for data storage**
- **Circuit breaker pattern for LLM API resilience**
- **Caching for improved performance**

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL 
- **LLM Providers**: Groq API or Ollama (local)
- **Authentication**: JWT-based auth with role-based access control
- **Deployment**: Docker, Docker Compose
- **Testing**: Pytest with coverage analysis

## Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Docker and Docker Compose (for containerized deployment)
- Groq API key (for cloud LLM)
- Nvidia GPU (optional, for local LLM)

## Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/exitbot.git
   cd exitbot
   ```

2. Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```
   
3. Edit the `.env` file to set your configuration:
   - Set `SECRET_KEY` to a secure random string
   - Configure database settings
   - Set your `GROQ_API_KEY` if using Groq

4. Start the application:
   ```bash
   # With Groq (cloud LLM)
   docker-compose up -d
   
   # With Ollama (local LLM)
   docker-compose --profile local_llm up -d
   ```

5. Access the application:
   - API: http://localhost:8000/api/v1
   - API documentation: http://localhost:8000/api/v1/docs

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/exitbot.git
   cd exitbot
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```

5. Configure your database:
   ```
   # For SQLite (development)
   DATABASE_URL=sqlite:///./exitbot.db
   
   # For PostgreSQL (production)
   DATABASE_URL=postgresql://user:password@localhost/exitbot
   ```

6. Run database migrations:
   ```bash
   alembic upgrade head
   ```

7. Start the application:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## API Documentation

The API documentation is available at `/api/v1/docs` when the application is running. It provides detailed information about all endpoints, request and response schemas, and authentication requirements.

## Running Tests

### Using Docker

```bash
docker-compose exec app python -m pytest
```

### Manual Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Generate coverage report
python -m pytest --cov=app --cov-report=html
```

## Environment Variables

See the `.env.example` file for all available configuration options. The most important ones are:

- `SECRET_KEY`: Secret key for JWT token generation (required)
- `DATABASE_URL`: Database connection string (required)
- `ENVIRONMENT`: Application environment (development, staging, production)
- `LLM_PROVIDER`: LLM provider to use (groq or ollama)
- `GROQ_API_KEY`: Groq API key (required if using Groq)
- `OLLAMA_HOST`: Ollama server URL (required if using Ollama)

## Deployment

The application can be deployed to any cloud provider that supports Docker containers. Here are some common options:

### AWS

1. Set up an ECR repository
2. Build and push the Docker image:
   ```bash
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<region>.amazonaws.com
   docker build -t <aws-account-id>.dkr.ecr.<region>.amazonaws.com/exitbot:latest .
   docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/exitbot:latest
   ```
3. Deploy using ECS, EKS, or EC2

### Digital Ocean

1. Create a DigitalOcean App
2. Connect to your GitHub repository
3. Configure environment variables
4. Deploy

### Heroku

1. Install the Heroku CLI
2. Log in to Heroku and create a new app:
   ```bash
   heroku login
   heroku create exitbot
   ```
3. Add PostgreSQL add-on:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```
4. Set environment variables:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set GROQ_API_KEY=your-groq-api-key
   # Add other variables as needed
   ```
5. Deploy the application:
   ```bash
   git push heroku main
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 

## Deployment Instructions

### Prerequisites

- Docker and Docker Compose
- PostgreSQL (or use the Docker Compose setup)
- Groq API key or Ollama instance

### Configuration

1. Clone the repository
2. Navigate to the project directory
3. Copy the environment template file:
   ```bash
   cp .env.template .env
   ```
4. Edit the `.env` file to configure your environment:
   - Update `SECRET_KEY` with a secure random string
   - Set `FIRST_ADMIN_EMAIL` and `FIRST_ADMIN_PASSWORD` for the admin user
   - Configure database settings if not using the default PostgreSQL
   - Set `LLM_PROVIDER` to either `groq` or `ollama`
   - If using Groq, set `GROQ_API_KEY` and `GROQ_MODEL`
   - If using Ollama, set `OLLAMA_BASE_URL` and `OLLAMA_MODEL`

### Deployment with Docker Compose

1. Build and start all services:
   ```bash
   docker-compose up -d
   ```

2. Check if all services are running:
   ```bash
   docker-compose ps
   ```

3. View logs:
   ```bash
   docker-compose logs -f
   ```

4. Access the application:
   - API: http://localhost:8000/api
   - Health check: http://localhost:8000/api/health

### Manual Installation

If you prefer to run the application without Docker:

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database:
   ```bash
   python -m app.scripts.migrate_db
   python -m app.scripts.create_admin
   ```

4. Start the application:
   ```bash
   python -m app.main
   ```

## Development

### Running Tests

```bash
pytest
```

### Running with Development Settings

For development, set `ENVIRONMENT=development` in your `.env` file to enable hot reload and additional logging. 