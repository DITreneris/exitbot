# ExitBot Scripts

This directory contains various scripts for deploying, testing, and maintaining the ExitBot application.

## Deployment Scripts

### Linux/Mac

- **`deploy.sh`**: Main deployment script for Linux/Mac environments
  ```bash
  # Deploy to production
  ./deploy.sh production
  
  # Deploy to staging
  ./deploy.sh staging
  
  # Deploy to development
  ./deploy.sh development
  ```

### Windows

- **`deploy.ps1`**: Main deployment script for Windows environments
  ```powershell
  # Deploy to production
  .\deploy.ps1 -Environment production
  
  # Deploy to staging
  .\deploy.ps1 -Environment staging
  
  # Deploy to development
  .\deploy.ps1 -Environment development
  ```

## Environment Setup

- **`setup_env.sh`**: Set up environment for Linux/Mac
- **`setup_env.bat`**: Set up environment for Windows

## Database Management

### Linux/Mac

- **`backup_db.sh`**: Create a database backup
  ```bash
  ./backup_db.sh
  ```

- **`restore_db.sh`**: Restore database from backup
  ```bash
  ./restore_db.sh ../backups/exitbot_db_20230501_120000.sql.gz
  ```

### Windows

- **`backup_db.ps1`**: Create a database backup (PowerShell)
  ```powershell
  .\backup_db.ps1
  ```

## Testing

- **`run_tests.sh`**: Run all tests and generate reports (Linux/Mac)
  ```bash
  ./run_tests.sh
  ```

- **`run_tests.ps1`**: Run all tests and generate reports (Windows)
  ```powershell
  .\run_tests.ps1
  ```

## Monitoring

- **`setup_monitoring.sh`**: Set up monitoring stack with Prometheus and Grafana
  ```bash
  ./setup_monitoring.sh
  ```

## Startup

- **`startup.sh`**: Startup script used by Docker containers

## Other Scripts

- **`optimize_db.py`**: Optimize database performance
  ```bash
  python optimize_db.py
  ```

- **`deploy_heroku.sh`**: Deploy to Heroku (legacy)

## Usage Notes

1. Make sure scripts have executable permissions on Linux/Mac:
   ```bash
   chmod +x *.sh
   ```

2. All scripts should be run from the scripts directory:
   ```bash
   cd scripts
   ./script_name.sh
   ```

3. Some scripts require Docker and Docker Compose to be installed and running.

4. For Windows PowerShell scripts, you may need to set the execution policy:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ``` 