---
title: Exit Interview Bot - Development Environment Setup Guide
category: Guide
audience: Developer
created: 2023-10-15
last_updated: 2025-05-01
version: 1.0
---

# Exit Interview Bot - Development Environment Setup

## Introduction

This guide will help you set up the development environment for the Exit Interview Bot project. Follow these steps to get your local development environment running properly.

## Prerequisites

- Python 3.9 or higher
- Git
- SQLite (for development)
- Groq API key (for LLM integration)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-organization/exit-interview-bot.git
cd exit-interview-bot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

#### Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root with the following variables:

```
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key_for_jwt
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password
```

### 5. Database Setup

Initialize the database:

```bash
python -m exitbot.app.database.init_db
```

Create an admin user:

```bash
python create_admin.py
```

## Running the Application

### 1. Start the Backend API

```bash
uvicorn exitbot.app.main:app --reload
```

The API will be available at http://localhost:8000

### 2. Start the Frontend Applications

#### Employee App:

```bash
streamlit run exitbot/employee_app.py
```

The Employee App will be available at http://localhost:8501

#### HR Dashboard:

```bash
streamlit run exitbot/hr_app.py
```

The HR Dashboard will be available at http://localhost:8502

## Development Workflow

1. Make changes to the codebase
2. Run tests: `pytest`
3. Check code style: `flake8 exitbot`
4. Submit a pull request

## Troubleshooting

### Common Issues

1. **Database Errors**
   
   If you encounter database errors, try resetting the database:
   
   ```bash
   rm exitbot.db
   python -m exitbot.app.database.init_db
   python create_admin.py
   ```

2. **API Connection Issues**
   
   Check that your Groq API key is valid and your network connection is stable.

3. **Streamlit Errors**
   
   Make sure you have the latest version of Streamlit installed:
   
   ```bash
   pip install --upgrade streamlit
   ```

## Additional Resources

- [API Documentation](../technical/api/api_reference.md)
- [Architecture Overview](../../planning/architecture/architecture_recommendations.md)
- [Implementation Plan](../../planning/implementation/implementation_plan.md)

---

*Last updated: 2025-05-01* 