#!/bin/bash
# Deploy to Heroku

# Install Heroku CLI if not installed
if ! command -v heroku &> /dev/null; then
    curl https://cli-assets.heroku.com/install.sh | sh
fi

# Login to Heroku
heroku login -i

# Push to Heroku
git push heroku main

# Run migrations
heroku run alembic upgrade head

# Check app status
heroku ps 