---
title: Exit Interview Bot - Predefined Questions Deployment Guide
category: Guide
audience: DevOps
created: 2025-05-01
last_updated: 2025-05-01
version: 1.0
---

# Predefined Questions System: Deployment Guide

## Overview

This guide provides instructions for deploying the new predefined questions system in the Exit Interview Bot. The new system replaces the LLM-based conversation flow with a structured sequence of fixed questions, improving reliability and reducing API costs.

## Prerequisites

Before deploying, ensure you have:

- Access to the application server and database
- Backup of the current database
- Sudo/admin privileges for service management
- The Exit Interview Bot repository with the predefined questions update

## Deployment Steps

### 1. Backup the Current System

```bash
# Backup the database
pg_dump -U <username> -d exitbot > exitbot_backup_$(date +%Y%m%d).sql

# Backup the application files
cp -r /path/to/exitbot /path/to/exitbot_backup_$(date +%Y%m%d)
```

### 2. Update Application Files

```bash
# Navigate to the application directory
cd /path/to/exitbot

# Pull the latest changes
git pull origin main

# Install any new dependencies
pip install -r requirements.txt
```

### 3. Database Updates

No schema changes are required for this update, as the existing database structure supports the new question flow. However, you should verify the database connection:

```bash
# Test database connection
python -c "from exitbot.app.db.database import get_db; next(get_db())"
```

### 4. Configuration Updates

If your deployment uses environment variables to configure LLM settings, these can remain in place but will be used less frequently. Update the following configuration:

```bash
# Edit the .env file
nano .env

# Set the new configuration values
USE_PREDEFINED_QUESTIONS=true
ALLOW_LLM_FALLBACK=false  # Set to true if you want to fall back to LLM for unanswered questions
```

### 5. Restart Services

```bash
# Restart the application service
sudo systemctl restart exitbot

# Restart the Nginx service if applicable
sudo systemctl restart nginx
```

### 6. Verify Deployment

1. Access the application URL in a browser
2. Log in as an employee user
3. Start a new exit interview
4. Verify that the first predefined question is displayed
5. Answer the question and confirm that the second question appears
6. Check the progress indicator appears correctly

### 7. Rollback Procedure (if needed)

If issues are encountered:

```bash
# Stop the services
sudo systemctl stop exitbot
sudo systemctl stop nginx

# Restore from backup
cd /path/to
rm -rf exitbot
cp -r exitbot_backup_<date> exitbot

# Restore database
psql -U <username> -d exitbot < exitbot_backup_<date>.sql

# Restart services
sudo systemctl start exitbot
sudo systemctl start nginx
```

## Monitoring

Monitor the application logs for any errors related to the predefined questions system:

```bash
# View application logs
tail -f /var/log/exitbot/app.log

# Look for specific errors
grep "ERROR" /var/log/exitbot/app.log
```

## Performance Considerations

The predefined questions system is expected to:

- Reduce response time by 60-80% as no LLM API calls are needed
- Lower operational costs by minimizing external API usage
- Increase reliability by eliminating dependency on external LLM services

## Additional Notes

- The previous LLM-based conversation code remains in the codebase but is not used by default
- No changes to user accounts or historical interview data will occur
- Interview reports will continue to work with both old and new interview data

## Support

For issues during deployment, contact:

- DevOps Team: devops@example.com
- Development Team: dev@example.com

For urgent concerns, use the on-call support system at extension 5555. 