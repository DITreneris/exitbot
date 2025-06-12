---
title: Exit Interview Bot - Architectural Recommendations
category: Planning
created: 2023-10-15
last_updated: 2025-05-01
version: 1.0
---

# Exit Interview Bot - Architectural Recommendations

## 1. Current Architecture Assessment

The Exit Interview Bot currently follows a traditional three-tier architecture:

1. **Presentation Layer**: Streamlit-based frontends (`hr_app.py` and `employee_app.py`)
2. **Application Layer**: FastAPI backend with business logic
3. **Data Layer**: SQLite database with SQLAlchemy ORM

While this structure provides a functional foundation, several architectural improvements can enhance maintainability, scalability, and reliability.

## 2. Key Architectural Challenges

1. **Tight Coupling**: Interview logic is tightly coupled with API endpoints
2. **Limited Abstraction**: Business logic leaks into different layers
3. **Monolithic Design**: No clear path for horizontal scaling
4. **Implicit State Management**: Interview state is inferred rather than explicitly modeled
5. **Direct Environment Access**: Configuration is scattered rather than centralized

## 3. Recommended Architecture

### 3.1 Domain-Driven Design Approach

Adopt a Domain-Driven Design (DDD) approach to clearly separate concerns and create a more maintainable codebase.

```
exitbot/
├── domain/                 # Core domain models and business logic
│   ├── interview/          # Interview domain
│   ├── user/               # User domain
│   └── reporting/          # Reporting domain
├── application/            # Application services
│   ├── commands/           # Command handlers
│   ├── queries/            # Query handlers
│   └── services/           # Cross-cutting services
├── infrastructure/         # External systems integration
│   ├── persistence/        # Database access
│   ├── llm/                # LLM integration
│   └── messaging/          # Event-based messaging
├── interfaces/             # API and UI interfaces
│   ├── api/                # FastAPI endpoints
│   └── web/                # Streamlit frontends
└── config/                 # Centralized configuration
```

### 3.2 CQRS Pattern Implementation

Implement Command Query Responsibility Segregation (CQRS) to separate read and write operations.

```python
# Command handler example
class CreateInterviewCommandHandler:
    def __init__(self, repository: InterviewRepository):
        self.repository = repository
    
    def handle(self, command: CreateInterviewCommand) -> Interview:
        interview = Interview(
            employee_id=command.employee_id,
            exit_date=command.exit_date,
            status="ACTIVE"
        )
        
        # Set initial question
        first_question = self.question_service.get_first_question()
        interview.set_current_question(first_question)
        
        # Save to repository
        self.repository.save(interview)
        return interview

# Query handler example
class GetInterviewDetailsQueryHandler:
    def __init__(self, repository: InterviewRepository):
        self.repository = repository
    
    def handle(self, query: GetInterviewDetailsQuery) -> InterviewDetails:
        interview = self.repository.get_by_id(query.interview_id)
        responses = self.repository.get_responses(query.interview_id)
        
        return InterviewDetails(
            interview=interview,
            responses=responses
        )
```

### 3.3 Event-Driven Architecture

Implement an event-driven approach for better decoupling and extensibility.

```python
# Event publishing
class InterviewService:
    def __init__(self, repository, event_publisher):
        self.repository = repository
        self.event_publisher = event_publisher
    
    def complete_interview(self, interview_id: int):
        interview = self.repository.get_by_id(interview_id)
        interview.complete()
        self.repository.save(interview)
        
        # Publish event
        self.event_publisher.publish(
            InterviewCompletedEvent(interview_id=interview_id)
        )

# Event subscription
class ReportingService:
    def __init__(self, report_repository):
        self.report_repository = report_repository
    
    def handle_interview_completed(self, event: InterviewCompletedEvent):
        # Generate report for completed interview
        report = self.generate_report(event.interview_id)
        self.report_repository.save(report)
        
        # Invalidate caches
        self.invalidate_report_caches()
```

### 3.4 Dependency Injection

Implement a formal dependency injection container to manage service dependencies.

```python
# Using a DI container (e.g., Python-dependency-injector)
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Repositories
    interview_repository = providers.Singleton(
        InterviewRepository,
        session_factory=db.session
    )
    
    # Services
    interview_service = providers.Singleton(
        InterviewService,
        repository=interview_repository,
        question_service=providers.Singleton(QuestionService)
    )
    
    # Command handlers
    create_interview_handler = providers.Singleton(
        CreateInterviewCommandHandler,
        repository=interview_repository
    )

# In FastAPI application
container = Container()
container.config.from_dict(settings.dict())

app = FastAPI()
app.container = container

@app.post("/api/interviews/")
def create_interview(
    command: CreateInterviewCommand,
    handler = Depends(lambda: app.container.create_interview_handler())
):
    return handler.handle(command)
```

### 3.5 State Machine Pattern for Interviews

Implement an explicit state machine for interview progression.

```python
from enum import Enum

class InterviewState(Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"

class Interview:
    def __init__(self, employee_id, exit_date):
        self.employee_id = employee_id
        self.exit_date = exit_date
        self.state = InterviewState.CREATED
        self.current_question_index = 0
        self.transitions = []
    
    def start(self):
        if self.state != InterviewState.CREATED:
            raise InvalidStateTransitionError("Cannot start an interview that is not in CREATED state")
        
        self.state = InterviewState.IN_PROGRESS
        self.transitions.append({"from": InterviewState.CREATED, "to": InterviewState.IN_PROGRESS, "timestamp": datetime.now()})
    
    def advance_question(self):
        if self.state != InterviewState.IN_PROGRESS:
            raise InvalidStateTransitionError("Cannot advance question when interview is not in progress")
        
        self.current_question_index += 1
        
        # Check if we've reached the end
        if self.current_question_index >= len(self.question_service.get_all_questions()):
            self.complete()
    
    def complete(self):
        if self.state != InterviewState.IN_PROGRESS:
            raise InvalidStateTransitionError("Cannot complete an interview that is not in progress")
        
        self.state = InterviewState.COMPLETED
        self.transitions.append({"from": InterviewState.IN_PROGRESS, "to": InterviewState.COMPLETED, "timestamp": datetime.now()})
    
    def abandon(self):
        if self.state == InterviewState.COMPLETED:
            raise InvalidStateTransitionError("Cannot abandon a completed interview")
        
        self.state = InterviewState.ABANDONED
        self.transitions.append({"from": self.state, "to": InterviewState.ABANDONED, "timestamp": datetime.now()})
```

## 4. Scalability Recommendations

### 4.1 Horizontal Scaling Strategy

1. **Stateless API Design**
   - Make all API endpoints stateless to enable horizontal scaling
   - Store session state in Redis or similar service

2. **Database Scalability**
   - Migrate from SQLite to PostgreSQL for production
   - Implement read replicas for reporting queries
   - Consider sharding for high-volume deployments

3. **Microservices Decomposition**
   - Extract interview, reporting, and authentication into separate services
   - Implement API gateway for unified external interface
   - Use message queues for inter-service communication

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   API Gateway │─────┤ Auth Service  │     │  Redis Cache  │
└───────┬───────┘     └───────────────┘     └───────────────┘
        │                     │                      │
┌───────┴───────┐     ┌───────┴───────┐     ┌───────┴───────┐
│  Interview    │─────┤  Reporting    │─────┤   User        │
│  Service      │     │  Service      │     │   Service     │
└───────────────┘     └───────────────┘     └───────────────┘
        │                     │                      │
┌───────┴───────┐     ┌───────┴───────┐     ┌───────┴───────┐
│  Interview DB  │     │  Report DB    │     │   User DB     │
└───────────────┘     └───────────────┘     └───────────────┘
```

### 4.2 Caching Strategy

1. **Multi-level Caching**
   - Implement application-level caching using Redis
   - Add response caching for frequently accessed endpoints
   - Implement client-side caching for UI assets

2. **Cache Invalidation Strategy**
   - Use event-based cache invalidation
   - Implement TTL (Time-To-Live) for all cached data
   - Add versioning to cached objects

```python
# Example caching service
class CacheService:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get_or_set(self, key, ttl_seconds, data_loader):
        # Try to get from cache
        cached_data = await self.redis.get(key)
        if cached_data:
            return json.loads(cached_data)
        
        # Load data if not in cache
        data = await data_loader()
        
        # Store in cache with TTL
        await self.redis.set(
            key, 
            json.dumps(data),
            expire=ttl_seconds
        )
        
        return data
    
    async def invalidate(self, pattern):
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

## 5. Resilience Patterns

### 5.1 Enhanced Circuit Breaker

Implement a more sophisticated circuit breaker pattern for external service calls.

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60, half_open_timeout=5):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        self.state = "CLOSED"
        self.failures = 0
        self.last_failure_time = None
        self.last_success_time = None
    
    async def execute(self, func, *args, **kwargs):
        if self.state == "OPEN":
            # Check if we should try half-open state
            if (datetime.now() - self.last_failure_time).total_seconds() > self.reset_timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError("Circuit is open")
        
        try:
            result = await func(*args, **kwargs)
            
            # Success - reset circuit if needed
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
            
            self.last_success_time = datetime.now()
            return result
            
        except Exception as e:
            self.failures += 1
            self.last_failure_time = datetime.now()
            
            # Check if we should open the circuit
            if self.failures >= self.failure_threshold or self.state == "HALF_OPEN":
                self.state = "OPEN"
            
            raise e
```

### 5.2 Bulkhead Pattern

Isolate different parts of the system to contain failures.

```python
class Bulkhead:
    def __init__(self, max_concurrent=10, max_queue_size=5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue_size = max_queue_size
        self.queue_count = 0
    
    async def execute(self, func, *args, **kwargs):
        if self.queue_count >= self.queue_size:
            raise BulkheadFullError("Bulkhead queue is full")
        
        self.queue_count += 1
        try:
            async with self.semaphore:
                self.queue_count -= 1
                return await func(*args, **kwargs)
        except Exception as e:
            self.queue_count -= 1
            raise e
```

### 5.3 Retry Pattern

Implement intelligent retry logic for transient failures.

```python
async def retry_with_backoff(func, max_retries=3, base_delay=1, backoff_factor=2):
    retries = 0
    while True:
        try:
            return await func()
        except TransientError as e:
            retries += 1
            if retries > max_retries:
                raise
            
            delay = base_delay * (backoff_factor ** (retries - 1))
            await asyncio.sleep(delay)
```

## 6. API Design Improvements

### 6.1 RESTful Resource Structure

Redesign API endpoints to follow consistent RESTful principles.

```
# Interview Resources
GET    /api/interviews                # List interviews
POST   /api/interviews                # Create interview
GET    /api/interviews/{id}           # Get interview details
PUT    /api/interviews/{id}           # Update interview
DELETE /api/interviews/{id}           # Delete interview

# Interview Messages
GET    /api/interviews/{id}/messages  # List all messages
POST   /api/interviews/{id}/messages  # Send a message
GET    /api/interviews/{id}/messages/{msg_id}  # Get specific message

# Reports
GET    /api/interviews/{id}/reports   # Get reports for interview
POST   /api/interviews/{id}/reports   # Generate new report
```

### 6.2 API Versioning

Implement proper API versioning to support backward compatibility.

```python
# In router definition
from fastapi import APIRouter

# V1 API
v1_router = APIRouter(prefix="/api/v1")

@v1_router.post("/interviews")
async def create_interview_v1(data: InterviewCreateV1Schema):
    # V1 implementation
    pass

# V2 API with new features
v2_router = APIRouter(prefix="/api/v2")

@v2_router.post("/interviews")
async def create_interview_v2(data: InterviewCreateV2Schema):
    # V2 implementation with enhanced features
    pass

# Add both routers to the app
app.include_router(v1_router)
app.include_router(v2_router)
```

## 7. Implementation Strategy

### 7.1 Incremental Refactoring Approach

1. **Phase 1: Core Domain Model Refactoring**
   - Extract interview domain logic into separate module
   - Implement state machine for interview progression
   - Keep existing APIs temporarily

2. **Phase 2: CQRS Implementation**
   - Add command and query handlers
   - Refactor APIs to use new handlers
   - Keep backward compatibility

3. **Phase 3: Event-Driven Architecture**
   - Implement event publishing/subscription
   - Refactor services to use events
   - Update APIs to use new event-driven flow

4. **Phase 4: Dependency Injection & Configuration**
   - Implement DI container
   - Centralize configuration
   - Update service instantiation

5. **Phase 5: Scalability Enhancements**
   - Implement caching layer
   - Add database optimizations
   - Prepare for horizontal scaling

### 7.2 Testing Strategy During Refactoring

1. Comprehensive test coverage before refactoring
2. Parallel implementations with feature flags
3. A/B testing of old vs. new architecture
4. Gradual migration of endpoints

## 8. Conclusion

The proposed architectural improvements address the current limitations while providing a clear path for future scalability and maintainability. By adopting domain-driven design, implementing CQRS and event-driven patterns, and enhancing the resilience of the system, the Exit Interview Bot can evolve into a robust enterprise application.

The incremental refactoring approach allows for these changes to be implemented while maintaining system stability and avoiding a complete rewrite. Each phase builds on the previous one, gradually transforming the architecture while continuing to deliver value to users. 