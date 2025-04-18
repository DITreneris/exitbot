# ExitBot Deployment Guide

This guide provides detailed instructions for deploying the ExitBot application in various environments.

## Deployment Options

ExitBot can be deployed in several ways:

1. **Docker Compose** - Recommended for most deployments
2. **Manual Installation** - For environments without Docker
3. **Production Deployment** - For high-availability production environments

## 1. Docker Compose Deployment

### Prerequisites

- Docker and Docker Compose installed
- Minimum system requirements:
  - 2 CPU cores
  - 4GB RAM
  - 10GB storage

### Steps

1. **Prepare Environment**

   Create a `.env` file from the template:
   ```bash
   cp .env.template .env
   ```

   Edit the `.env` file to configure your environment variables:
   ```
   # Required settings
   SECRET_KEY=your_secure_random_string
   FIRST_ADMIN_EMAIL=admin@example.com
   FIRST_ADMIN_PASSWORD=strong_password
   
   # LLM settings - choose one provider
   LLM_PROVIDER=groq  # or ollama
   GROQ_API_KEY=your_groq_api_key
   ```

2. **Start the Services**

   Build and start all services:
   ```bash
   docker-compose up -d
   ```

3. **Verify Deployment**

   Check service status:
   ```bash
   docker-compose ps
   ```

   All services should be in the "Up" state.

4. **Access the Application**

   - API: http://localhost:8000/api
   - Health check: http://localhost:8000/api/health

### Troubleshooting

- **Database Connection Issues**
  - Check PostgreSQL logs: `docker-compose logs db`
  - Verify database environment variables in `.env`

- **API Not Responding**
  - Check application logs: `docker-compose logs app`
  - Verify network connectivity between services

## 2. Manual Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database
- Virtual environment tool (venv, conda, etc.)

### Steps

1. **Create Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Configure Environment**

   Create a `.env` file:
   ```bash
   cp .env.template .env
   ```

   Edit the `.env` file to configure database connection and other settings.

4. **Initialize Database**

   ```bash
   python -m app.scripts.migrate_db
   python -m app.scripts.create_admin
   ```

5. **Start the Application**

   ```bash
   python -m app.main
   ```

   The API will be available at http://localhost:8000.

## 3. Production Deployment

For production environments, consider the following additional steps:

### Security Considerations

1. **Use a Reverse Proxy**

   Configure Nginx or Apache as a reverse proxy with HTTPS.

2. **Database Security**

   - Use strong passwords
   - Configure PostgreSQL for security
   - Consider using managed database services

3. **Environment Variables**

   - Use a proper secrets management system
   - Don't store sensitive information in files

### High Availability

1. **Load Balancing**

   Deploy multiple application instances behind a load balancer.

2. **Database Redundancy**

   Configure PostgreSQL replication for failover.

3. **Monitoring**

   Set up monitoring and alerting for all components.

## Deployment Checklist

Before going live, verify:

- [ ] All environment variables are properly configured
- [ ] Database migrations run successfully
- [ ] Admin user can be created
- [ ] API endpoints are accessible
- [ ] LLM integration works correctly
- [ ] Backups are configured
- [ ] Logging is set up correctly
- [ ] Monitoring is in place

## Maintenance

Regular maintenance tasks include:

1. **Backups**

   Schedule regular database backups:
   ```bash
   pg_dump -U postgres exitbot > exitbot_backup_$(date +%Y%m%d).sql
   ```

2. **Updates**

   To update the application:
   ```bash
   git pull
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

3. **Logs Rotation**

   Configure log rotation for application logs. 