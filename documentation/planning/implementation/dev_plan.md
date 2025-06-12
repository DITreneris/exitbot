# ExitBot MVP Development Plan

## Project Overview
ExitBot is a Python-based conversational bot that conducts structured exit interviews with departing employees, collects feedback, and generates reports for HR using Groq (with LLaMa3) for fast and high-quality LLM inference.

## Development Goals
1. Create a functional conversational HR exit interview bot
2. Implement secure data collection and reporting
3. Provide intuitive interfaces for both employees and HR
4. Ensure high-performance with Groq's LLaMa3 integration
5. Deliver a maintainable, extensible codebase

## Project Structure
```
exitbot/
├── app/                      # Main application code
│   ├── api/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication routes
│   │   ├── interview.py      # Interview routes
│   │   └── reports.py        # Reporting routes
│   ├── core/                 # Core application components
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration management
│   │   ├── security.py       # Security utilities
│   │   └── logging.py        # Logging configuration
│   ├── db/                   # Database related code
│   │   ├── __init__.py
│   │   ├── base.py           # Base DB setup
│   │   ├── models.py         # SQLAlchemy models
│   │   └── crud.py           # CRUD operations
│   ├── llm/                  # LLM integration
│   │   ├── __init__.py
│   │   ├── factory.py        # LLM factory for provider selection
│   │   ├── groq_client.py    # Groq API integration
│   │   ├── ollama_client.py  # Ollama integration (alternative)
│   │   ├── client_base.py    # Base LLM client with resilience features
│   │   └── prompts.py        # Prompt templates
│   ├── schemas/              # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py           # Auth schemas
│   │   ├── interview.py      # Interview schemas
│   │   └── report.py         # Report schemas
│   └── services/             # Business logic
│       ├── __init__.py
│       ├── interview.py      # Interview logic
│       ├── reporting.py      # Reporting logic
│       └── caching.py        # Caching service for performance
├── frontend/                 # Streamlit frontend
│   ├── __init__.py
│   ├── employee_app.py       # Employee interview interface
│   ├── hr_app.py             # HR dashboard
│   └── components/           # Reusable components
├── tests/                    # Test suite
├── .env.example              # Example environment variables
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Docker configuration
├── main.py                   # Application entry point
└── requirements.txt          # Python dependencies
```

## Development Roadmap

### Phase 1: Foundation (Week 1)

#### Day 1-2: Project Setup
- [x] Create requirements.txt file
- [x] Set up project structure
- [x] Create configuration management with environment variables
- [x] Setup basic logging system
- [x] Initialize git repository
  - [x] Initial commit pushed to `https://github.com/DITreneris/exitbot`

#### Day 3-5: Database Implementation
- [x] Define SQLAlchemy models:
  - [x] Users (employees, HR admins)
  - [x] Interview sessions
  - [x] Questions and responses
  - [x] Reports
- [x] Create database migration scripts
- [x] Implement CRUD operations
- [x] Set up database connection handling

### Phase 2: Core Backend (Week 2)

#### Day 1-3: Authentication & API Foundation
- [x] Implement JWT authentication for HR admins
- [x] Implement simple token for employee interviews
- [x] Create FastAPI application structure
- [x] Set up middleware (CORS, error handling)
- [x] Implement basic health check endpoints

#### Day 4-5: LLM Integration
- [x] Design flexible LLM provider factory pattern
- [x] Implement Groq client with error handling and retries
- [x] Create backup Ollama client for local deployment
- [x] Define interview prompt templates
- [x] Implement conversation state management
- [x] Create basic sentiment analysis function
- [x] Test Groq connectivity and response handling
- [x] Implement circuit breaker pattern for resilience
- [x] Add exponential backoff for API failures

### Phase 3: Interview Logic (Week 3)

#### Day 1-3: Interview Flow
- [x] Implement question sequence management
- [x] Create interview session handling
- [x] Implement dynamic follow-up questions
- [x] Add response validation and sanitization
- [x] Build interview data persistence

#### Day 4-5: API Endpoints
- [x] Create interview initiation endpoint
- [x] Implement message exchange endpoint
- [x] Add interview completion and submission
- [x] Create interview retrieval endpoints
- [x] Add basic reporting endpoints
- [x] Enhance OpenAPI documentation for endpoints

### Phase 4: Frontend Development (Week 4)

#### Day 1-3: Employee Interface
- [x] Create Streamlit chat interface
- [x] Implement authentication flow
- [x] Build responsive message display
- [x] Add progress indicator for interview stages
- [x] Implement interview submission confirmation

#### Day 4-5: HR Dashboard
- [x] Create HR login and authentication
- [x] Build interview listing and filtering
- [x] Implement individual interview view
- [x] Create basic report visualization
- [x] Add CSV/JSON export functionality

### Phase 5: Integration & Testing (Week 5)

#### Day 1-2: Integration Testing
- [x] Write integration tests for API endpoints
- [x] Test end-to-end interview flow
- [x] Validate data persistence
- [x] Test report generation
- [x] Verify authentication flows
- [x] Final test suite run confirms 91/91 tests passing.

#### Day 3-4: User Experience Refinement
- [x] Improve error handling and resilience
- [x] Implement TTL-based caching for performance
- [x] Resolved all (4) pytest warnings (`PytestCollectionWarning`, `PytestReturnNotNoneWarning`) for a clean test suite.
- [x] Enhance UI responsiveness
- [x] Add loading indicators
- [x] Review and improve accessibility

#### Day 5: Documentation
- [x] Document API endpoints
- [x] Create setup instructions
- [x] Write README with Groq/Ollama integration details
- [x] Document system architecture
- [x] Prepare deployment instructions

### Phase 6: Deployment (Week 6)

#### Day 1-2: Containerization
- [x] Create Dockerfile for application
- [x] Configure Docker Compose for local deployment
- [x] Test containerized application
- [x] Optimize container size and performance

#### Day 3-4: Deployment Setup
- [x] Prepare deployment scripts
- [x] Configure environment variables
- [x] Set up database initialization
- [x] Configure production logging
- [x] Test deployment on target environment

#### Day 5: Final Testing & Launch
- [x] Conduct final end-to-end testing
- [x] Verify security measures
- [x] Check performance metrics
- [x] Create deployment documentation
- [x] Launch MVP

## Key Implementation Details

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    department VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

#### Interviews Table
```sql
CREATE TABLE interviews (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES users(id),
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'in_progress',
    exit_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Questions Table
```sql
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    order_num INTEGER,
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);
```

#### Responses Table
```sql
CREATE TABLE responses (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interviews(id),
    question_id INTEGER REFERENCES questions(id),
    employee_message TEXT,
    bot_response TEXT,
    sentiment FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints

#### Authentication
- POST `/api/auth/login` - User login
- POST `/api/auth/employee-access` - Create employee access token

#### Interviews
- POST `/api/interviews/start` - Start a new interview
- POST `/api/interviews/{interview_id}/message` - Send/receive messages
- PUT `/api/interviews/{interview_id}/complete` - Complete an interview
- GET `/api/interviews` - List interviews (HR only)
- GET `/api/interviews/{interview_id}` - Get specific interview

#### Reports
- GET `/api/reports/summary` - Get summary statistics
- GET `/api/reports/by-department` - Get department breakdown
- GET `/api/reports/export` - Export data as CSV/JSON

## Current Progress

All planned development tasks have been successfully completed. The ExitBot MVP is now ready for launch, with the following accomplishments:

### LLM Client Architecture
- BaseLLMClient implements robust error handling with circuit breaker pattern
- Provider-specific implementations for Ollama (local) and Groq (cloud)
- Factory pattern for client instantiation and provider selection
- Comprehensive retry logic with exponential backoff

### Interview Conversation Flow
- Well-structured prompt system for different interview stages
- Message history maintained for context during conversations
- Sentiment analysis of employee responses

### API Integration
- Clearly defined endpoints for interview management
- Secure authentication and authorization checks
- Role-based access control for administrators and employees

### Deployment and Performance
- Docker and Heroku deployment configuration completed
- Performance optimizations implemented:
  - Database query optimization with indexes
  - LLM response caching with TTL
  - Circuit breaker pattern for resilience
- Comprehensive deployment documentation created
- Upgraded from Pydantic v1 to v2:
  - Updated validators (`validator` to `field_validator`, `root_validator` to `model_validator`)
  - Replaced `Config` classes with `model_config` dictionaries
  - Changed `orm_mode=True` to `from_attributes=True`
  - Updated import paths for Pydantic settings

### Documentation and Testing
- API endpoints fully documented
- User guides for both HR administrators and employees
- Security review completed
- End-to-end testing verified in production environment

The ExitBot MVP has been successfully developed, tested, and is now ready for production use. 