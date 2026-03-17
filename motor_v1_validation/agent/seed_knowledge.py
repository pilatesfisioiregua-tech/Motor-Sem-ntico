"""Seed knowledge_base with ~57 curated technical entries across 8 categories."""

import os
import sys
import psycopg2

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgres://postgres:postgres@localhost:15432/postgres"
)

ENTRIES = [
    # ================================================================
    # ARCHITECTURE (10 entries)
    # ================================================================
    {
        "title": "Clean Architecture — Dependency Rule",
        "category": "architecture",
        "content": """The Dependency Rule (Robert C. Martin, Clean Architecture 2017): source code dependencies must point inward — from frameworks/drivers → interface adapters → use cases → entities.

PRACTICAL APPLICATION:
- Entities: pure domain objects, no framework imports
- Use Cases: application logic, depends only on entities
- Adapters: convert external data to/from use case format
- Frameworks: FastAPI routes, DB drivers, external APIs

PYTHON EXAMPLE:
```python
# entities/user.py — NO imports from frameworks
@dataclass
class User:
    id: str
    email: str
    def is_active(self) -> bool: ...

# use_cases/register.py — depends only on entities + interfaces
class RegisterUser:
    def __init__(self, repo: UserRepository, mailer: Mailer): ...
    async def execute(self, email: str, password: str) -> User: ...

# adapters/postgres_repo.py — implements interface, depends on framework
class PostgresUserRepository(UserRepository):
    def __init__(self, pool: asyncpg.Pool): ...
```

ANTI-PATTERNS:
- Importing SQLAlchemy models in use cases
- Business logic in FastAPI route handlers
- Entities that know about serialization formats

Source: Clean Architecture — Robert C. Martin (2017), Chapter 22"""
    },
    {
        "title": "SOLID Principles — Practical Python Guide",
        "category": "architecture",
        "content": """SOLID principles applied to Python with real examples.

S — Single Responsibility: A class should have one reason to change.
```python
# BAD: UserService handles auth + email + persistence
# GOOD: AuthService, EmailService, UserRepository — each with one job
```

O — Open/Closed: Open for extension, closed for modification.
```python
# Use Protocol/ABC + strategy pattern instead of if/elif chains
class PaymentProcessor(Protocol):
    def process(self, amount: Decimal) -> Receipt: ...

# Add new processors without modifying existing code
class StripeProcessor: ...
class PayPalProcessor: ...
```

L — Liskov Substitution: Subtypes must be substitutable for base types.
```python
# BAD: Square inherits Rectangle but breaks set_width/set_height contract
# GOOD: Both implement Shape protocol independently
```

I — Interface Segregation: Clients shouldn't depend on methods they don't use.
```python
# BAD: one fat Repository with 20 methods
# GOOD: ReadRepository, WriteRepository, SearchRepository
```

D — Dependency Inversion: Depend on abstractions, not concretions.
```python
# BAD: def send_alert(slack: SlackClient)
# GOOD: def send_alert(notifier: Notifier)  # Protocol
```

Source: Design Principles and Design Patterns — Robert C. Martin (2000)"""
    },
    {
        "title": "Domain-Driven Design — Tactical Patterns",
        "category": "architecture",
        "content": """DDD tactical patterns for complex business logic (Eric Evans, 2003).

ENTITIES: Objects with identity that persists across state changes.
```python
class Order:
    id: OrderId  # identity
    items: list[OrderItem]
    status: OrderStatus
    def add_item(self, product: Product, qty: int) -> None: ...
    def cancel(self) -> None: ...
```

VALUE OBJECTS: Immutable, compared by attributes, no identity.
```python
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str
    def __add__(self, other: 'Money') -> 'Money': ...
```

AGGREGATES: Cluster of entities with a root that enforces invariants.
- All modifications go through the aggregate root
- Only reference other aggregates by ID, never by object

REPOSITORIES: Abstract persistence, return aggregates.
```python
class OrderRepository(Protocol):
    async def get(self, id: OrderId) -> Order: ...
    async def save(self, order: Order) -> None: ...
```

DOMAIN EVENTS: Record that something happened.
```python
@dataclass(frozen=True)
class OrderPlaced:
    order_id: str
    customer_id: str
    total: Money
    occurred_at: datetime
```

ANTI-PATTERNS:
- Anemic domain model (entities with only getters/setters, logic in services)
- Aggregate too large (include only what's needed to enforce invariants)
- Crossing aggregate boundaries in a single transaction

Source: Domain-Driven Design — Eric Evans (2003)"""
    },
    {
        "title": "12-Factor App Methodology",
        "category": "architecture",
        "content": """The 12-Factor App (Heroku, 2012) — principles for cloud-native applications.

1. CODEBASE: One codebase tracked in VCS, many deploys
2. DEPENDENCIES: Explicitly declare and isolate (requirements.txt, pyproject.toml)
3. CONFIG: Store in environment variables, never in code
```python
# GOOD
DATABASE_URL = os.environ["DATABASE_URL"]
# BAD
DATABASE_URL = "postgres://user:pass@prod-db:5432/mydb"
```
4. BACKING SERVICES: Treat as attached resources (DB, cache, queue)
5. BUILD, RELEASE, RUN: Strictly separate stages
6. PROCESSES: Execute as stateless processes — no sticky sessions
7. PORT BINDING: Export services via port binding (fly.io internal_port)
8. CONCURRENCY: Scale out via process model, not threading
9. DISPOSABILITY: Fast startup, graceful shutdown
```python
@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()
    await http_client.aclose()
```
10. DEV/PROD PARITY: Keep environments as similar as possible
11. LOGS: Treat as event streams (stdout, not files)
12. ADMIN PROCESSES: Run as one-off processes (migrations, seeds)

ANTI-PATTERNS:
- Storing state in local filesystem (use S3/DB instead)
- Hardcoded config values
- Long startup times (>30s)

Source: https://12factor.net — Adam Wiggins (2012)"""
    },
    {
        "title": "GoF Design Patterns — Most Used in Python",
        "category": "architecture",
        "content": """Gang of Four patterns most relevant to modern Python (Gamma et al., 1994).

STRATEGY: Swap algorithms at runtime.
```python
# Python-native: just pass a function
def process_data(data: list, sorter: Callable = sorted) -> list:
    return sorter(data)
```

OBSERVER: Publish/subscribe for event-driven systems.
```python
class EventBus:
    _handlers: dict[str, list[Callable]] = defaultdict(list)
    def subscribe(self, event: str, handler: Callable): ...
    def publish(self, event: str, data: Any): ...
```

FACTORY: Create objects without specifying concrete class.
```python
def create_llm_client(provider: str) -> LLMClient:
    match provider:
        case "anthropic": return AnthropicClient()
        case "openai": return OpenAIClient()
        case _: raise ValueError(f"Unknown: {provider}")
```

DECORATOR: Add behavior without modifying class (Python has native decorators).
```python
@retry(max_attempts=3, backoff=2.0)
@log_execution_time
async def call_api(prompt: str) -> str: ...
```

SINGLETON: In Python, use module-level instances instead of class pattern.
```python
# settings.py — module IS the singleton
_settings = None
def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

ANTI-PATTERNS:
- Over-applying patterns where simple functions suffice
- AbstractFactoryFactoryBuilder (Java-itis)
- Singleton for things that should be injected

Source: Design Patterns — Gamma, Helm, Johnson, Vlissides (1994)"""
    },
    {
        "title": "Event-Driven Architecture Patterns",
        "category": "architecture",
        "content": """Event-driven patterns for decoupled, scalable systems.

EVENT SOURCING: Store state as sequence of events, not current state.
```python
# Instead of UPDATE users SET name='X' WHERE id=1
# Store: UserNameChanged(user_id=1, old='Y', new='X', at=now)
events = event_store.get_events(aggregate_id)
state = reduce(apply_event, events, initial_state)
```

CQRS: Separate read models from write models.
- Commands: validate + append events
- Queries: read from denormalized projections
- Benefit: optimize read/write independently

SAGA PATTERN: Manage distributed transactions via compensating actions.
```python
# Book flight → Book hotel → Charge card
# If charge fails: cancel hotel → cancel flight (compensations)
class BookingSaga:
    steps = [book_flight, book_hotel, charge_card]
    compensations = [cancel_flight, cancel_hotel, refund_card]
```

OUTBOX PATTERN: Reliable event publishing with DB transactions.
```python
async with transaction():
    await save_order(order)
    await save_to_outbox(OrderCreated(order.id))
# Separate process polls outbox → publishes to message queue
```

WHEN TO USE:
- Multiple services need to react to state changes
- Audit trail is important
- Systems need to be independently scalable

WHEN NOT TO USE:
- Simple CRUD apps
- Strong consistency required across all reads
- Team unfamiliar with eventual consistency

Source: Designing Data-Intensive Applications — Martin Kleppmann (2017), Ch. 11"""
    },
    {
        "title": "API Design — REST Best Practices",
        "category": "architecture",
        "content": """REST API design principles for consistency and usability.

URL STRUCTURE:
```
GET    /api/v1/users          # list
POST   /api/v1/users          # create
GET    /api/v1/users/{id}     # read
PUT    /api/v1/users/{id}     # full update
PATCH  /api/v1/users/{id}     # partial update
DELETE /api/v1/users/{id}     # delete
GET    /api/v1/users/{id}/orders  # nested resource
```

STATUS CODES:
- 200 OK, 201 Created, 204 No Content
- 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity
- 500 Internal Server Error, 503 Service Unavailable

PAGINATION:
```python
@app.get("/users")
async def list_users(limit: int = 20, offset: int = 0):
    return {"data": users[offset:offset+limit], "total": len(users),
            "limit": limit, "offset": offset}
```

ERROR FORMAT (consistent):
```json
{"error": {"code": "VALIDATION_ERROR", "message": "Email required",
           "details": [{"field": "email", "issue": "missing"}]}}
```

VERSIONING: URL prefix (/api/v1/) over headers for simplicity.

ANTI-PATTERNS:
- Verbs in URLs (/getUser, /createOrder)
- Returning 200 with error body
- Nested resources >2 levels deep
- Not using proper HTTP methods (POST for everything)

Source: REST API Design Rulebook — Mark Masse (2011)"""
    },
    {
        "title": "Hexagonal Architecture (Ports & Adapters)",
        "category": "architecture",
        "content": """Hexagonal Architecture (Alistair Cockburn, 2005) isolates business logic from infrastructure.

STRUCTURE:
```
domain/          # Core business logic, no external dependencies
  models.py      # Entities, Value Objects
  services.py    # Business rules
  ports.py       # Interfaces (Protocol classes)

adapters/
  inbound/       # Drive the application (API, CLI, events)
    api.py       # FastAPI routes → call domain services
    cli.py       # CLI commands → call domain services
  outbound/      # Driven by the application (DB, APIs, email)
    postgres.py  # Implements RepositoryPort
    anthropic.py # Implements LLMPort
    smtp.py      # Implements EmailPort
```

PORTS (interfaces):
```python
class UserRepository(Protocol):
    async def find_by_id(self, id: str) -> User | None: ...
    async def save(self, user: User) -> None: ...

class LLMClient(Protocol):
    async def complete(self, prompt: str) -> str: ...
```

ADAPTERS (implementations):
```python
class PostgresUserRepo:
    def __init__(self, pool: asyncpg.Pool): ...
    async def find_by_id(self, id: str) -> User | None:
        row = await self.pool.fetchrow("SELECT ...", id)
        return User(**row) if row else None
```

BENEFITS:
- Swap DB without touching business logic
- Test domain with in-memory adapters
- Clear dependency direction (adapters depend on domain, never reverse)

Source: Hexagonal Architecture — Alistair Cockburn (2005)"""
    },
    {
        "title": "Microservices Communication Patterns",
        "category": "architecture",
        "content": """Patterns for inter-service communication in distributed systems.

SYNCHRONOUS (request/response):
- HTTP/REST: simple, well-understood, higher coupling
- gRPC: binary protocol, code generation, good for internal comms
- Best for: queries that need immediate response

ASYNCHRONOUS (event-driven):
- Message Queue (RabbitMQ, SQS): point-to-point, guaranteed delivery
- Pub/Sub (Kafka, NATS): broadcast, event log, replay capability
- Best for: fire-and-forget, event notifications, decoupling

PATTERNS:
1. API Gateway: Single entry point, routing, auth, rate limiting
2. Service Mesh: Infrastructure-level networking (Istio, Linkerd)
3. Circuit Breaker: Prevent cascade failures
```python
@circuit_breaker(failure_threshold=5, recovery_timeout=30)
async def call_payment_service(order_id: str): ...
```
4. Bulkhead: Isolate resources per service
5. Retry with Exponential Backoff:
```python
for attempt in range(max_retries):
    try:
        return await call_service()
    except TransientError:
        await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
```

ANTI-PATTERNS:
- Distributed monolith (services tightly coupled via sync calls)
- Shared database between services
- Chatty interfaces (many small calls instead of batch)

Source: Building Microservices — Sam Newman (2021, 2nd ed.)"""
    },
    {
        "title": "Architectural Decision Records (ADR)",
        "category": "architecture",
        "content": """ADR: lightweight documentation for significant architecture decisions.

TEMPLATE (Michael Nygard format):
```markdown
# ADR-001: Use PostgreSQL with pgvector for embeddings

## Status
Accepted

## Context
We need vector similarity search for semantic routing.
Options: pgvector, Pinecone, Weaviate, ChromaDB.

## Decision
Use pgvector extension in existing fly.io Postgres.

## Consequences
- Good: No new infrastructure, SQL-native queries, lower cost
- Bad: Less optimized than dedicated vector DB at scale
- Neutral: Need to manage index tuning ourselves

## Alternatives Considered
- Pinecone: SaaS cost ~$70/mo, another dependency
- ChromaDB: embedded, good for dev, not production-grade
```

RULES:
- One decision per ADR, numbered sequentially
- Never delete or modify — supersede with new ADR
- Store in docs/adr/ or decisions/ directory
- Review ADRs quarterly for relevance

WHEN TO WRITE:
- Choosing a framework, database, or major library
- Defining API contracts or data formats
- Changing deployment strategy
- NOT for: implementation details, code style choices

Source: Documenting Architecture Decisions — Michael Nygard (2011)"""
    },

    # ================================================================
    # PYTHON (8 entries)
    # ================================================================
    {
        "title": "Python async/await — Patterns and Pitfalls",
        "category": "python",
        "content": """Async Python patterns for I/O-bound applications (FastAPI, DB, HTTP calls).

CONCURRENT EXECUTION:
```python
# Run independent coroutines concurrently
results = await asyncio.gather(
    fetch_user(user_id),
    fetch_orders(user_id),
    fetch_preferences(user_id),
)
user, orders, prefs = results

# With error handling
results = await asyncio.gather(*tasks, return_exceptions=True)
for r in results:
    if isinstance(r, Exception):
        logger.error(f"Task failed: {r}")
```

SEMAPHORE for rate limiting:
```python
sem = asyncio.Semaphore(10)  # max 10 concurrent

async def fetch_with_limit(url: str):
    async with sem:
        return await http_client.get(url)

# Process 1000 URLs, max 10 at a time
results = await asyncio.gather(*[fetch_with_limit(u) for u in urls])
```

TIMEOUT:
```python
try:
    result = await asyncio.wait_for(slow_operation(), timeout=30.0)
except asyncio.TimeoutError:
    logger.warning("Operation timed out")
```

CONNECTION POOLS (always use them):
```python
# asyncpg
pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
async with pool.acquire() as conn:
    rows = await conn.fetch("SELECT ...")

# httpx
async with httpx.AsyncClient(limits=httpx.Limits(max_connections=20)) as client:
    resp = await client.get(url)
```

ANTI-PATTERNS:
- Running sync code in async function (blocks event loop)
- Creating new connections per request instead of using pool
- asyncio.gather with unbounded tasks (OOM risk)
- Forgetting to await a coroutine (returns coroutine object, not result)

Source: Fluent Python, 2nd ed. — Luciano Ramalho (2022), Ch. 21"""
    },
    {
        "title": "Python Type Hints — Production Patterns",
        "category": "python",
        "content": """Type hints for maintainable Python codebases.

BASICS:
```python
def process(name: str, count: int = 1) -> list[str]: ...
def fetch(url: str) -> dict[str, Any]: ...
def find(id: str) -> User | None: ...  # Python 3.10+
```

GENERICS:
```python
from typing import TypeVar, Generic
T = TypeVar("T")

class Repository(Generic[T]):
    async def get(self, id: str) -> T | None: ...
    async def save(self, entity: T) -> None: ...

class UserRepo(Repository[User]): ...
```

PROTOCOL (structural subtyping):
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict: ...

def save(obj: Serializable) -> None:
    data = obj.to_dict()  # type-safe
```

TYPEDDICT for structured dicts:
```python
class APIResponse(TypedDict):
    status: str
    data: list[dict[str, Any]]
    total: int
```

CALLABLE:
```python
Handler = Callable[[Request], Awaitable[Response]]
Middleware = Callable[[Handler], Handler]
```

TOOLS:
- mypy: strict static checker (`mypy --strict src/`)
- pyright: faster, used by Pylance in VSCode
- beartype: runtime type checking for critical paths

ANTI-PATTERNS:
- `Any` everywhere (defeats the purpose)
- Ignoring mypy errors with `# type: ignore` without reason
- Over-typing simple scripts that don't need it

Source: Effective Python, 3rd ed. — Brett Slatkin (2024)"""
    },
    {
        "title": "FastAPI — Production Configuration",
        "category": "python",
        "content": """FastAPI production patterns and configuration.

APP STRUCTURE:
```python
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create pools, load models
    app.state.db = await asyncpg.create_pool(DATABASE_URL)
    app.state.http = httpx.AsyncClient()
    yield
    # Shutdown: cleanup
    await app.state.db.close()
    await app.state.http.aclose()

app = FastAPI(lifespan=lifespan, docs_url="/docs" if DEV else None)
```

DEPENDENCY INJECTION:
```python
async def get_db(request: Request) -> asyncpg.Pool:
    return request.app.state.db

@app.get("/users/{id}")
async def get_user(id: str, db: asyncpg.Pool = Depends(get_db)):
    return await db.fetchrow("SELECT * FROM users WHERE id=$1", id)
```

ERROR HANDLING:
```python
@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=400, content={"error": exc.message})
```

MIDDLEWARE:
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response
```

PERFORMANCE:
- Use uvicorn with --workers for multi-process
- Connection pooling for all external services
- Response streaming for large payloads
- Background tasks for non-blocking operations

Source: FastAPI documentation — Sebastián Ramírez (tiangolo)"""
    },
    {
        "title": "Python Error Handling — Best Practices",
        "category": "python",
        "content": """Error handling patterns for robust Python applications.

EXCEPTION HIERARCHY:
```python
class AppError(Exception):
    \"\"\"Base application error.\"\"\"
    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code

class NotFoundError(AppError):
    def __init__(self, entity: str, id: str):
        super().__init__(f"{entity} {id} not found", "NOT_FOUND")

class ValidationError(AppError):
    def __init__(self, field: str, issue: str):
        super().__init__(f"{field}: {issue}", "VALIDATION_ERROR")
```

CONTEXT MANAGERS for cleanup:
```python
@contextmanager
def temporary_file(suffix: str = ".tmp"):
    path = tempfile.mktemp(suffix=suffix)
    try:
        yield path
    finally:
        os.unlink(path) if os.path.exists(path) else None
```

RETRY with backoff:
```python
async def retry_async(fn, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return await fn()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
```

STRUCTURED LOGGING on errors:
```python
except Exception as e:
    logger.error("operation_failed",
                 error=str(e), error_type=type(e).__name__,
                 user_id=user_id, operation="create_order")
    raise
```

ANTI-PATTERNS:
- Bare `except:` (catches SystemExit, KeyboardInterrupt)
- `except Exception: pass` (silent failures)
- Catching too broad, re-raising without context
- Using exceptions for flow control

Source: Effective Python — Brett Slatkin (2024), Items 65-70"""
    },
    {
        "title": "Python Dataclasses and Pydantic — When to Use What",
        "category": "python",
        "content": """Choosing between dataclasses and Pydantic for data modeling.

DATACLASSES — for internal domain objects:
```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class User:
    id: str
    email: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: list[str] = field(default_factory=list)

@dataclass(frozen=True)  # immutable value object
class Money:
    amount: Decimal
    currency: str = "EUR"
```

PYDANTIC — for external boundaries (API, config, validation):
```python
from pydantic import BaseModel, Field, field_validator

class CreateUserRequest(BaseModel):
    email: str = Field(..., pattern=r'^[\\w.-]+@[\\w.-]+\\.\\w+$')
    name: str = Field(..., min_length=1, max_length=100)

    @field_validator('email')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    created_at: datetime
```

DECISION GUIDE:
| Criteria | dataclass | Pydantic |
|----------|-----------|----------|
| Validation needed | No | Yes |
| External input | No | Yes |
| Performance critical | Yes | No (slower) |
| JSON serialization | Manual | Built-in |
| Domain model | Yes | No (use for DTOs) |

ANTI-PATTERNS:
- Using Pydantic for everything (overhead for internal objects)
- Using dataclasses for API input (no validation)
- Mixing domain logic into Pydantic models

Source: Pydantic v2 docs + Fluent Python (Ramalho, 2022)"""
    },
    {
        "title": "Python Testing — pytest Patterns",
        "category": "python",
        "content": """Testing patterns with pytest for reliable test suites.

FIXTURES:
```python
@pytest.fixture
async def db_pool():
    pool = await asyncpg.create_pool(TEST_DATABASE_URL)
    yield pool
    await pool.close()

@pytest.fixture
def mock_llm():
    with patch("src.utils.llm_client.call_anthropic") as mock:
        mock.return_value = {"content": "mocked response"}
        yield mock
```

PARAMETRIZE:
```python
@pytest.mark.parametrize("input,expected", [
    ("hello world", ["hello", "world"]),
    ("", []),
    ("single", ["single"]),
])
def test_tokenize(input, expected):
    assert tokenize(input) == expected
```

ASYNC TESTS:
```python
import pytest

@pytest.mark.asyncio
async def test_fetch_user(db_pool):
    user = await fetch_user(db_pool, "user-1")
    assert user.email == "test@example.com"
```

TEST STRUCTURE (Arrange-Act-Assert):
```python
def test_order_total():
    # Arrange
    order = Order(items=[Item(price=10), Item(price=20)])
    # Act
    total = order.calculate_total()
    # Assert
    assert total == Money(30, "EUR")
```

MOCKING EXTERNAL SERVICES:
```python
@pytest.fixture
def mock_anthropic(respx_mock):
    respx_mock.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(200, json={"content": [{"text": "ok"}]})
    )
```

ANTI-PATTERNS:
- Testing implementation details instead of behavior
- Tests that depend on execution order
- Mocking everything (test nothing)
- No assertions (test that "doesn't crash" tests nothing)

Source: Python Testing with pytest — Brian Okken (2022)"""
    },
    {
        "title": "Python Performance — Profiling and Optimization",
        "category": "python",
        "content": """Performance optimization workflow: measure first, optimize second.

PROFILING:
```python
# cProfile for function-level
python -m cProfile -s cumulative script.py

# line_profiler for line-level
@profile
def hot_function():
    ...
kernprof -l -v script.py

# memory_profiler
@profile
def memory_heavy():
    ...
python -m memory_profiler script.py
```

COMMON OPTIMIZATIONS:
```python
# 1. Use generators for large sequences
def process_large_file(path: str):
    with open(path) as f:
        for line in f:  # lazy, not f.readlines()
            yield parse(line)

# 2. dict/set for O(1) lookups
valid_ids = set(load_ids())  # not list
if user_id in valid_ids: ...  # O(1) vs O(n)

# 3. List comprehension > loop + append
result = [transform(x) for x in data if x.valid]

# 4. __slots__ for memory-heavy objects
class Point:
    __slots__ = ('x', 'y')
    def __init__(self, x: float, y: float):
        self.x = x; self.y = y

# 5. functools.lru_cache for expensive pure functions
@lru_cache(maxsize=256)
def fibonacci(n: int) -> int: ...
```

ASYNC PERFORMANCE:
- asyncio.gather() for concurrent I/O
- Connection pools (don't create per-request)
- Semaphores to limit concurrency
- uvloop for 2-4x event loop speedup

ANTI-PATTERNS:
- Premature optimization without profiling
- Optimizing code that runs once
- Using threads for I/O-bound work (use async)
- Loading entire datasets into memory

Source: High Performance Python — Gorelick & Ozsvald (2020)"""
    },
    {
        "title": "Python Logging — Structured Logging with structlog",
        "category": "python",
        "content": """Structured logging setup for production Python applications.

SETUP:
```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),  # prod
        # structlog.dev.ConsoleRenderer(),    # dev
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()
```

USAGE:
```python
# Structured key-value pairs
logger.info("request_processed", method="POST", path="/api/users",
            status=201, duration_ms=45)

# Bind context for request lifecycle
log = logger.bind(request_id=request.state.request_id, user_id=user.id)
log.info("order_created", order_id=order.id)
log.info("payment_processed", amount=order.total)

# Context variables (auto-propagate through async calls)
structlog.contextvars.bind_contextvars(request_id="abc-123")
# All subsequent log calls include request_id
```

OUTPUT (JSON, one line per event):
```json
{"event": "request_processed", "method": "POST", "path": "/api/users",
 "status": 201, "duration_ms": 45, "level": "info",
 "timestamp": "2024-01-15T10:30:00Z"}
```

ANTI-PATTERNS:
- f-string in log messages: `logger.info(f"User {id}")` — can't aggregate
- Logging sensitive data (passwords, tokens, PII)
- Using print() instead of logging
- Not setting log levels per environment

Source: structlog documentation + 12-Factor App (logging)"""
    },

    # ================================================================
    # DATABASE (8 entries)
    # ================================================================
    {
        "title": "PostgreSQL Indexing — When and How",
        "category": "database",
        "content": """PostgreSQL index strategies for query performance.

B-TREE (default, most common):
```sql
CREATE INDEX idx_users_email ON users (email);
-- Best for: equality (=), range (<, >), ORDER BY, LIKE 'prefix%'
```

GIN (Generalized Inverted Index):
```sql
CREATE INDEX idx_docs_content ON documents USING gin(to_tsvector('english', content));
-- Best for: full-text search, JSONB containment, array operations
CREATE INDEX idx_data_jsonb ON events USING gin(metadata jsonb_path_ops);
```

PARTIAL INDEX (index subset of rows):
```sql
CREATE INDEX idx_active_users ON users (email) WHERE status = 'active';
-- Smaller index, faster queries when filtering by status='active'
```

COMPOSITE INDEX (multi-column):
```sql
CREATE INDEX idx_orders_user_date ON orders (user_id, created_at DESC);
-- Serves: WHERE user_id = X ORDER BY created_at DESC
-- Column order matters! Most selective first for equality, range last
```

COVERING INDEX (include extra columns):
```sql
CREATE INDEX idx_users_email_cover ON users (email) INCLUDE (name, avatar_url);
-- Index-only scan: no table lookup needed
```

DIAGNOSIS:
```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...;
-- Look for: Seq Scan (bad on large tables), high actual rows vs estimated
-- Check: pg_stat_user_indexes for unused indexes
```

ANTI-PATTERNS:
- Index every column (slows writes, wastes space)
- Missing index on foreign keys (slow JOINs)
- Not using EXPLAIN ANALYZE before and after
- Indexing low-cardinality columns (boolean, status with 3 values)

Source: Use the Index, Luke — Markus Winand (https://use-the-index-luke.com)"""
    },
    {
        "title": "PostgreSQL Connection Pooling — asyncpg and PgBouncer",
        "category": "database",
        "content": """Connection management for Python + PostgreSQL applications.

ASYNCPG POOL (application-level):
```python
import asyncpg

pool = await asyncpg.create_pool(
    DATABASE_URL,
    min_size=2,       # keep 2 connections warm
    max_size=10,      # max 10 concurrent connections
    max_inactive_connection_lifetime=300,  # recycle after 5min idle
    command_timeout=30,
)

# Usage — always use context manager
async with pool.acquire() as conn:
    rows = await conn.fetch("SELECT * FROM users WHERE id=$1", user_id)

# Transactions
async with pool.acquire() as conn:
    async with conn.transaction():
        await conn.execute("INSERT INTO ...", ...)
        await conn.execute("UPDATE ...", ...)
```

PGBOUNCER (proxy-level):
- Transaction pooling: connection returned after each transaction
- Session pooling: connection held for entire session
- Use transaction mode for serverless/high-connection-count

SIZING:
- Formula: connections = (CPU cores * 2) + effective_spindle_count
- For fly.io shared-cpu-2x: ~5-10 connections max
- More connections ≠ better: context switching overhead

FLY.IO POSTGRES SPECIFICS:
```python
# fly proxy forwards to internal Postgres
# Local dev: postgres://postgres:pass@localhost:15432/postgres
# In-app: use internal DNS postgres://user:pass@app-db.internal:5432/db
```

ANTI-PATTERNS:
- Creating connection per request (connection storm)
- Pool too large for server (each conn = ~10MB RAM)
- Not closing connections (connection leak)
- Forgetting to set statement_timeout

Source: PostgreSQL docs + asyncpg documentation"""
    },
    {
        "title": "PostgreSQL Query Optimization Patterns",
        "category": "database",
        "content": """Common query patterns and optimizations for PostgreSQL.

BATCH OPERATIONS:
```sql
-- BAD: N+1 inserts
INSERT INTO items (name) VALUES ('a');
INSERT INTO items (name) VALUES ('b');

-- GOOD: single multi-row insert
INSERT INTO items (name) VALUES ('a'), ('b'), ('c');

-- asyncpg batch
await conn.executemany(
    "INSERT INTO items (name, price) VALUES ($1, $2)",
    [("a", 10), ("b", 20), ("c", 30)]
)
```

UPSERT (INSERT ON CONFLICT):
```sql
INSERT INTO knowledge_base (title, content, category)
VALUES ($1, $2, $3)
ON CONFLICT (title) DO UPDATE SET
    content = EXCLUDED.content,
    updated_at = NOW();
```

CTE for complex queries:
```sql
WITH active_users AS (
    SELECT id, email FROM users WHERE status = 'active'
),
recent_orders AS (
    SELECT user_id, count(*) as order_count
    FROM orders WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY user_id
)
SELECT u.email, COALESCE(o.order_count, 0)
FROM active_users u
LEFT JOIN recent_orders o ON u.id = o.user_id;
```

WINDOW FUNCTIONS:
```sql
SELECT user_id, amount,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as rn,
    SUM(amount) OVER (PARTITION BY user_id) as total
FROM orders;
```

ANTI-PATTERNS:
- SELECT * (fetch only needed columns)
- N+1 queries (use JOINs or batch fetch)
- Not using prepared statements (SQL injection + no plan cache)
- OFFSET for pagination on large tables (use keyset pagination)

Source: The Art of PostgreSQL — Dimitri Fontaine (2020)"""
    },
    {
        "title": "Database Migration Best Practices",
        "category": "database",
        "content": """Safe database migration patterns for production systems.

PRINCIPLES:
1. Every migration must be idempotent (safe to re-run)
2. Every migration must have a rollback path
3. Separate schema changes from data migrations
4. Never lock tables for long in production

SAFE PATTERNS:
```sql
-- Adding a column (safe, no lock):
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- Adding index concurrently (no table lock):
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users (email);

-- Adding NOT NULL with default (safe in PG 11+):
ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'active';
```

DANGEROUS PATTERNS (avoid in production):
```sql
-- Locks entire table while rewriting:
ALTER TABLE users ALTER COLUMN email SET NOT NULL;
-- Safe alternative: add CHECK constraint first
ALTER TABLE users ADD CONSTRAINT email_not_null CHECK (email IS NOT NULL) NOT VALID;
ALTER TABLE users VALIDATE CONSTRAINT email_not_null;

-- Never rename columns in production (breaks running code)
-- Instead: add new column → backfill → deploy new code → drop old column
```

MIGRATION FILE FORMAT:
```sql
-- migration: 20240115_add_user_status.sql
-- description: Add status column to users table
-- rollback: ALTER TABLE users DROP COLUMN IF EXISTS status;

BEGIN;
ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_status ON users (status);
COMMIT;
```

ANTI-PATTERNS:
- Running migrations during peak traffic
- No rollback plan
- Mixing schema + data migration in one file
- Not testing migration on staging first

Source: PostgreSQL docs + Zero Downtime Migrations (Braintree)"""
    },
    {
        "title": "PostgreSQL JSONB — When and How to Use",
        "category": "database",
        "content": """JSONB in PostgreSQL: flexible schema within relational database.

WHEN TO USE JSONB:
- Schema varies per row (user preferences, metadata, event payloads)
- Nested data that doesn't need relational queries
- Rapid prototyping before schema stabilizes

WHEN NOT TO USE:
- Data you'll query/filter frequently (use columns)
- Data with referential integrity needs
- Large text blobs (use TEXT)

OPERATIONS:
```sql
-- Create with JSONB column
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert
INSERT INTO events (type, payload) VALUES
('order_created', '{"order_id": "123", "items": [{"sku": "A1", "qty": 2}]}');

-- Query nested fields
SELECT payload->>'order_id' as order_id,
       payload->'items'->0->>'sku' as first_sku
FROM events WHERE type = 'order_created';

-- Filter by JSONB content
SELECT * FROM events WHERE payload @> '{"order_id": "123"}';

-- Update nested field
UPDATE events SET payload = jsonb_set(payload, '{status}', '"shipped"')
WHERE payload->>'order_id' = '123';
```

INDEXING:
```sql
-- GIN index for containment queries (@>, ?, ?|, ?&)
CREATE INDEX idx_events_payload ON events USING gin(payload jsonb_path_ops);

-- Expression index for specific field
CREATE INDEX idx_events_order_id ON events ((payload->>'order_id'));
```

ANTI-PATTERNS:
- Putting everything in JSONB (relational data belongs in columns)
- No GIN index on queried JSONB columns
- Using JSON instead of JSONB (no indexing, slower)

Source: PostgreSQL 16 Documentation, Chapter 8.14"""
    },
    {
        "title": "Database Transaction Isolation Levels",
        "category": "database",
        "content": """Transaction isolation levels and their practical implications.

LEVELS (PostgreSQL):
1. READ COMMITTED (default): See committed data at statement start
2. REPEATABLE READ: See committed data at transaction start
3. SERIALIZABLE: Full isolation, as if transactions ran sequentially

PRACTICAL GUIDE:
```sql
-- Read Committed (default, fine for most cases)
BEGIN;
SELECT balance FROM accounts WHERE id = 1;  -- sees latest committed
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;

-- Repeatable Read (consistent snapshots)
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SELECT sum(balance) FROM accounts;  -- consistent view
-- Any concurrent modification to accounts → serialization error
COMMIT;

-- Serializable (strongest, use sparingly)
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
-- Full serializability guarantee
-- Higher chance of serialization failures → must retry
COMMIT;
```

COMMON ISSUES:
- Lost Update: Two transactions read, modify, write same row
  Fix: SELECT ... FOR UPDATE or serializable isolation
- Phantom Read: New rows appear between reads in same transaction
  Fix: Repeatable Read or Serializable

```python
# Handling serialization failures in asyncpg
for attempt in range(3):
    try:
        async with conn.transaction(isolation='repeatable_read'):
            await conn.execute(...)
            break
    except asyncpg.SerializationError:
        if attempt == 2: raise
        await asyncio.sleep(0.1 * (2 ** attempt))
```

ANTI-PATTERNS:
- Using SERIALIZABLE for everything (performance cost)
- Long-running transactions (hold locks, block others)
- Not handling serialization failures with retry

Source: DDIA — Martin Kleppmann (2017), Chapter 7"""
    },
    {
        "title": "pgvector — Vector Search in PostgreSQL",
        "category": "database",
        "content": """Using pgvector for semantic search and embeddings in PostgreSQL.

SETUP:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 dimension
    metadata JSONB DEFAULT '{}'
);
```

INDEXING (critical for performance):
```sql
-- IVFFlat: faster build, good for <1M vectors
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- lists ≈ sqrt(num_rows)

-- HNSW: better recall, slower build, better for >100K vectors
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

QUERIES:
```sql
-- Cosine similarity (most common for text embeddings)
SELECT id, content, 1 - (embedding <=> $1::vector) AS similarity
FROM documents
ORDER BY embedding <=> $1::vector
LIMIT 10;

-- L2 distance
SELECT * FROM documents ORDER BY embedding <-> $1::vector LIMIT 10;

-- Inner product
SELECT * FROM documents ORDER BY embedding <#> $1::vector LIMIT 10;
```

PYTHON INTEGRATION:
```python
# asyncpg with pgvector
import numpy as np

embedding = await get_embedding(text)  # from Anthropic/OpenAI
await conn.execute(
    "INSERT INTO documents (content, embedding) VALUES ($1, $2)",
    text, str(embedding.tolist())
)

# Search
results = await conn.fetch(
    "SELECT content, 1-(embedding <=> $1::vector) as sim "
    "FROM documents ORDER BY embedding <=> $1::vector LIMIT $2",
    str(query_embedding.tolist()), 10
)
```

ANTI-PATTERNS:
- No index on vector column (full table scan)
- Wrong distance metric for your embeddings
- Storing too-high-dimension vectors (>2000 dims slow)
- Not setting probes parameter for IVFFlat queries

Source: pgvector GitHub + PostgreSQL documentation"""
    },
    {
        "title": "Database Backup and Recovery Strategies",
        "category": "database",
        "content": """Backup strategies for PostgreSQL in production.

FLY.IO POSTGRES:
```bash
# Automatic daily snapshots (fly.io manages)
fly postgres backup list -a db-app-name

# Manual snapshot
fly postgres backup create -a db-app-name

# Restore from snapshot
fly postgres backup restore <snapshot-id> -a db-app-name
```

PG_DUMP (logical backup):
```bash
# Full backup
pg_dump -Fc -h localhost -p 15432 -U postgres dbname > backup.dump

# Specific tables
pg_dump -Fc -t knowledge_base -t users dbname > partial.dump

# Restore
pg_restore -h localhost -p 15432 -U postgres -d dbname backup.dump

# Schema only
pg_dump --schema-only dbname > schema.sql
```

CONTINUOUS ARCHIVING (WAL):
- Point-in-time recovery (PITR)
- fly.io Postgres includes WAL archiving
- Can restore to any point in time within retention window

STRATEGY BY SIZE:
| DB Size | Strategy | RPO | RTO |
|---------|----------|-----|-----|
| <1GB | pg_dump daily + before deploys | 24h | 5min |
| 1-100GB | WAL archiving + daily base backup | ~0 | 15min |
| >100GB | WAL + incremental (pgBackRest) | ~0 | varies |

BEFORE RISKY OPERATIONS:
```bash
# Always backup before migrations
pg_dump -Fc dbname > pre_migration_$(date +%Y%m%d).dump
# Run migration
# If failed: pg_restore
```

ANTI-PATTERNS:
- No backups (obviously)
- Backups but never tested restore
- Only logical backups for large DBs (slow restore)
- Storing backups on same server as database

Source: PostgreSQL docs + fly.io Postgres documentation"""
    },

    # ================================================================
    # SECURITY (6 entries)
    # ================================================================
    {
        "title": "OWASP Top 10 — Python/FastAPI Prevention",
        "category": "security",
        "content": """OWASP Top 10 (2021) with Python/FastAPI specific mitigations.

A01 BROKEN ACCESS CONTROL:
```python
# Always verify ownership
@app.get("/orders/{order_id}")
async def get_order(order_id: str, user: User = Depends(get_current_user)):
    order = await db.fetch_order(order_id)
    if order.user_id != user.id:
        raise HTTPException(403, "Not your order")
```

A02 CRYPTOGRAPHIC FAILURES:
```python
# Never store plaintext passwords
from passlib.context import CryptContext
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_ctx.hash(password)
verified = pwd_ctx.verify(password, hashed)

# Use secrets for tokens
import secrets
token = secrets.token_urlsafe(32)
```

A03 INJECTION:
```python
# ALWAYS use parameterized queries
await conn.fetch("SELECT * FROM users WHERE id=$1", user_id)  # GOOD
await conn.fetch(f"SELECT * FROM users WHERE id='{user_id}'")  # SQL INJECTION

# Pydantic validates input automatically
class UserInput(BaseModel):
    name: str = Field(max_length=100, pattern=r'^[a-zA-Z ]+$')
```

A05 SECURITY MISCONFIGURATION:
```python
# Disable docs in production
app = FastAPI(docs_url="/docs" if os.getenv("ENV") == "dev" else None)

# CORS — restrict origins
app.add_middleware(CORSMiddleware,
    allow_origins=["https://myapp.com"],  # NOT ["*"]
    allow_methods=["GET", "POST"])
```

A07 AUTHENTICATION FAILURES:
- Rate limit login attempts
- Use strong password policies
- Implement MFA for sensitive operations

A09 SECURITY LOGGING:
```python
logger.warning("auth_failure", ip=request.client.host,
               email=attempt_email, reason="invalid_password")
```

Source: OWASP Top 10 (2021) — https://owasp.org/Top10/"""
    },
    {
        "title": "API Key and Secret Management",
        "category": "security",
        "content": """Managing API keys and secrets in production applications.

ENVIRONMENT VARIABLES (baseline):
```python
# settings.py
import os

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]

# Never: hardcode keys, commit .env files, log secrets
```

FLY.IO SECRETS:
```bash
# Set secrets (encrypted at rest)
fly secrets set ANTHROPIC_API_KEY=sk-ant-xxx -a app-name

# List (shows names, not values)
fly secrets list -a app-name

# Import from file
fly secrets import < .env.prod -a app-name
```

KEY ROTATION PATTERN:
```python
# Multiple keys for rotation
KEYS = [os.environ.get(f"ANTHROPIC_API_KEY_{i}") for i in range(1, 5)]
KEYS = [k for k in KEYS if k]  # filter None

class KeyRotator:
    def __init__(self, keys: list[str]):
        self._keys = keys
        self._index = 0

    def next(self) -> str:
        key = self._keys[self._index % len(self._keys)]
        self._index += 1
        return key
```

WHAT NEVER TO DO:
- Commit .env, credentials.json, or any secret to git
- Log API keys or tokens (even partially)
- Share keys between environments (dev/staging/prod)
- Use same key for multiple services
- Hardcode keys in Dockerfiles or docker-compose

.GITIGNORE:
```
.env
.env.*
*.pem
*.key
credentials.json
```

Source: NIST SP 800-57 + 12-Factor App (Config)"""
    },
    {
        "title": "Input Validation and Sanitization",
        "category": "security",
        "content": """Input validation patterns to prevent injection and data corruption.

VALIDATION LAYERS:
1. API boundary (Pydantic models)
2. Business logic (domain validation)
3. Database (constraints, types)

PYDANTIC VALIDATION:
```python
from pydantic import BaseModel, Field, field_validator
import re

class CreateUserRequest(BaseModel):
    email: str = Field(..., max_length=254)
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=150)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r'^[\\w.+-]+@[\\w-]+\\.[\\w.]+$', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()

    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return re.sub(r'[<>&\"\\']', '', v).strip()
```

PATH TRAVERSAL PREVENTION:
```python
import os

def safe_read_file(base_dir: str, filename: str) -> str:
    # Resolve to absolute path and check it's within base_dir
    safe_path = os.path.realpath(os.path.join(base_dir, filename))
    if not safe_path.startswith(os.path.realpath(base_dir)):
        raise ValueError("Path traversal detected")
    return open(safe_path).read()
```

COMMAND INJECTION PREVENTION:
```python
# NEVER use shell=True with user input
import subprocess
subprocess.run(["ls", "-la", user_path], shell=False)  # GOOD
subprocess.run(f"ls -la {user_path}", shell=True)       # DANGEROUS
```

ANTI-PATTERNS:
- Validating only on frontend (backend must validate too)
- Blocklist approach (block known bad vs allow known good)
- Trusting data from "internal" services without validation

Source: OWASP Input Validation Cheat Sheet"""
    },
    {
        "title": "HTTPS, CORS, and Security Headers",
        "category": "security",
        "content": """Web security headers and CORS configuration for FastAPI.

CORS CONFIGURATION:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com", "https://staging.myapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,  # preflight cache
)
```

SECURITY HEADERS MIDDLEWARE:
```python
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response
```

FLY.IO HTTPS:
- fly.io handles TLS termination automatically
- force_https = true in fly.toml
- Internal traffic between services is encrypted via WireGuard

RATE LIMITING:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/login")
@limiter.limit("5/minute")
async def login(request: Request): ...
```

ANTI-PATTERNS:
- CORS allow_origins=["*"] with credentials
- No rate limiting on auth endpoints
- HTTP in production (always HTTPS)
- Missing security headers

Source: MDN Web Security + OWASP Secure Headers Project"""
    },
    {
        "title": "JWT and Session-Based Authentication",
        "category": "security",
        "content": """Authentication patterns for Python/FastAPI applications.

JWT (stateless):
```python
from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = os.environ["JWT_SECRET"]
ALGORITHM = "HS256"

def create_token(user_id: str, expires_hours: int = 24) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=expires_hours),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(401, "Invalid token")
```

FASTAPI DEPENDENCY:
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: asyncpg.Pool = Depends(get_db),
) -> User:
    payload = verify_token(creds.credentials)
    user = await db.fetchrow("SELECT * FROM users WHERE id=$1", payload["sub"])
    if not user:
        raise HTTPException(401, "User not found")
    return User(**user)
```

JWT vs SESSIONS:
| Aspect | JWT | Session |
|--------|-----|---------|
| Storage | Client (cookie/header) | Server (Redis/DB) |
| Stateless | Yes | No |
| Revocation | Hard (need blocklist) | Easy (delete session) |
| Scalability | Better (no shared state) | Needs shared store |
| Best for | APIs, microservices | Traditional web apps |

ANTI-PATTERNS:
- Storing sensitive data in JWT payload (it's base64, not encrypted)
- No token expiration
- JWT secret too short or predictable
- Not validating token on every request

Source: OWASP Authentication Cheat Sheet + python-jose docs"""
    },
    {
        "title": "Dependency Vulnerability Scanning",
        "category": "security",
        "content": """Managing and scanning dependencies for known vulnerabilities.

TOOLS:
```bash
# pip-audit: scan Python deps for CVEs
pip install pip-audit
pip-audit                    # scan current environment
pip-audit -r requirements.txt  # scan requirements file

# safety: alternative scanner
pip install safety
safety check

# GitHub Dependabot: auto-creates PRs for vulnerable deps
# Enable in repo Settings > Security > Dependabot alerts
```

PINNING DEPENDENCIES:
```
# requirements.txt — pin exact versions in production
fastapi==0.109.0
uvicorn==0.27.0
asyncpg==0.29.0
anthropic==0.18.1

# Use pip-compile (pip-tools) to generate pinned from abstract deps
# requirements.in (abstract)
fastapi>=0.109
# pip-compile requirements.in → requirements.txt (pinned with hashes)
```

UPDATE STRATEGY:
1. Dependabot/Renovate for automatic PR creation
2. Run tests before merging dependency updates
3. Update minor/patch weekly, major monthly
4. Always check CHANGELOG before major upgrades

DOCKER IMAGE SCANNING:
```bash
# Trivy: scan Docker images
trivy image myapp:latest

# Snyk: scan and monitor
snyk container test myapp:latest
```

ANTI-PATTERNS:
- Unpinned dependencies in production
- Ignoring security advisories
- Using abandoned/unmaintained packages
- Not scanning Docker base images

Source: OWASP Dependency-Check + pip-audit documentation"""
    },

    # ================================================================
    # DEVOPS (6 entries)
    # ================================================================
    {
        "title": "fly.io Deployment — Production Checklist",
        "category": "devops",
        "content": """fly.io deployment best practices and operational patterns.

FLY.TOML CONFIGURATION:
```toml
app = "my-app"
primary_region = "cdg"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8080"
  PYTHONUNBUFFERED = "1"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0

  [http_service.concurrency]
    type = "requests"
    hard_limit = 25
    soft_limit = 20

[[vm]]
  size = "shared-cpu-2x"
  memory = "512mb"
```

DEPLOYMENT:
```bash
fly deploy --remote-only            # build on fly.io builders
fly deploy --strategy rolling       # zero-downtime deploy
fly status                          # check deployment status
fly logs                            # stream application logs
fly ssh console                     # SSH into running machine
```

SECRETS:
```bash
fly secrets set KEY=value -a app-name
fly secrets list -a app-name
fly secrets unset KEY -a app-name
```

POSTGRES:
```bash
fly postgres create --name db-app
fly postgres attach db-app -a my-app   # sets DATABASE_URL
fly proxy 15432:5432 -a db-app         # local access
```

SCALING:
```bash
fly scale count 2                    # 2 machines
fly scale vm shared-cpu-2x           # change VM size
fly autoscale set min=1 max=5        # autoscaling
```

HEALTH CHECKS:
```python
@app.get("/health")
async def health():
    # Check critical dependencies
    try:
        await db_pool.fetchval("SELECT 1")
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return JSONResponse(503, {"status": "error", "db": str(e)})
```

Source: fly.io documentation (https://fly.io/docs/)"""
    },
    {
        "title": "Docker — Python Production Dockerfile",
        "category": "devops",
        "content": """Optimized Dockerfile patterns for Python applications.

MULTI-STAGE BUILD:
```dockerfile
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app

# Copy only installed packages
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/

# Non-root user
RUN useradd -m appuser
USER appuser

EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

OPTIMIZATION TIPS:
1. Order layers by change frequency (deps before code)
2. Use .dockerignore to exclude unnecessary files
3. Pin base image version (python:3.12.1-slim, not python:latest)
4. Minimize layers (combine RUN commands)
5. Use slim/alpine base images

.DOCKERIGNORE:
```
.git
.env
.env.*
__pycache__
*.pyc
.pytest_cache
.mypy_cache
tests/
docs/
*.md
```

HEALTH CHECK IN DOCKERFILE:
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD curl -f http://localhost:8080/health || exit 1
```

ANTI-PATTERNS:
- Running as root in container
- Using :latest tag (non-reproducible builds)
- COPY . . without .dockerignore (includes .env, .git)
- Installing dev dependencies in production image
- Not using multi-stage builds (bloated images)

Source: Docker Best Practices — Docker documentation"""
    },
    {
        "title": "CI/CD Pipeline — GitHub Actions for Python",
        "category": "devops",
        "content": """GitHub Actions CI/CD pipeline for Python projects.

BASIC PIPELINE:
```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest --cov=src --cov-report=xml
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/postgres
      - uses: codecov/codecov-action@v4

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

CACHING:
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

SECRETS: Store in GitHub Settings > Secrets and variables > Actions

ANTI-PATTERNS:
- No CI at all (merging untested code)
- Deploying from local machine instead of CI
- Not caching dependencies (slow builds)
- Running full test suite on every tiny change (use path filters)

Source: GitHub Actions documentation"""
    },
    {
        "title": "Monitoring and Observability",
        "category": "devops",
        "content": """Observability pillars: logs, metrics, traces.

STRUCTURED LOGGING (see Python logging entry):
```python
logger.info("request_handled", method="POST", path="/api/execute",
            status=200, duration_ms=1250, model="sonnet")
```

METRICS (Prometheus pattern):
```python
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter('http_requests_total', 'Total requests',
                       ['method', 'path', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds',
                            'Request duration', ['method', 'path'])
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active DB connections')

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_DURATION.labels(request.method, request.url.path).observe(duration)
    return response
```

HEALTH CHECK PATTERN:
```python
@app.get("/health")
async def health():
    checks = {}
    checks["db"] = await check_db()
    checks["llm"] = await check_llm_api()
    all_ok = all(c["status"] == "ok" for c in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "healthy" if all_ok else "degraded", "checks": checks}
    )
```

FLY.IO METRICS:
```bash
fly metrics             # Built-in metrics dashboard
fly logs --region cdg   # Region-specific logs
```

ALERTING RULES (general):
- Error rate > 5% for 5 minutes → P1
- p99 latency > 10s for 10 minutes → P2
- Health check failing → P1
- Cost anomaly (>2x daily average) → P2

Source: Google SRE Book — Beyer et al. (2016), Chapter 6"""
    },
    {
        "title": "Git Workflow — Trunk-Based Development",
        "category": "devops",
        "content": """Trunk-based development workflow for small teams.

WORKFLOW:
1. main branch is always deployable
2. Short-lived feature branches (<1 day ideally, <3 days max)
3. Small, frequent PRs (prefer 50-200 lines changed)
4. CI must pass before merge
5. Deploy from main automatically

BRANCH NAMING:
```
feat/add-user-auth
fix/connection-pool-leak
refactor/split-router
docs/api-reference
```

COMMIT MESSAGES (Conventional Commits):
```
feat: add API key rotation with 4-key round-robin
fix: connection pool exhaustion under concurrent load
refactor: extract LLM client into separate module
docs: add ADR for pgvector decision
chore: update dependencies to latest patch versions
```

PR CHECKLIST:
- [ ] Tests pass
- [ ] No new warnings
- [ ] Follows existing code patterns
- [ ] No secrets in diff
- [ ] Migration is reversible
- [ ] Updated relevant documentation

WHEN TO BRANCH LONGER:
- Breaking changes that need feature flags
- Large refactors (but prefer incremental)
- Experimental features

ANTI-PATTERNS:
- Long-lived branches (merge hell)
- Direct pushes to main without CI
- Giant PRs (>500 lines = hard to review)
- Merge commits instead of rebase (messy history)

Source: Trunk Based Development — https://trunkbaseddevelopment.com"""
    },
    {
        "title": "Infrastructure as Code — fly.io Patterns",
        "category": "devops",
        "content": """Infrastructure management patterns for fly.io deployments.

MULTI-APP SETUP:
```bash
# Separate apps for separation of concerns
fly apps create chief-os-omni      # Code OS agent
fly apps create motor-semantico     # Motor pipeline
fly apps create omni-db             # Shared Postgres

# Each with its own fly.toml
fly.codeos.toml    → chief-os-omni
fly.toml           → motor-semantico
```

ENVIRONMENT MANAGEMENT:
```bash
# Staging
fly deploy -a my-app-staging --config fly.staging.toml
fly secrets set ENV=staging -a my-app-staging

# Production
fly deploy -a my-app --config fly.toml
fly secrets set ENV=production -a my-app
```

DATABASE MANAGEMENT:
```bash
# Create Postgres cluster
fly postgres create --name omni-db --region cdg --vm-size shared-cpu-1x

# Attach to app (sets DATABASE_URL automatically)
fly postgres attach omni-db -a chief-os-omni

# Proxy for local access
fly proxy 15432:5432 -a omni-db

# Connect via psql
psql postgres://postgres:password@localhost:15432/postgres
```

DEPLOYMENT AUTOMATION:
```bash
#!/bin/bash
# scripts/deploy.sh
set -euo pipefail

APP=${1:-chief-os-omni}
CONFIG=${2:-fly.codeos.toml}

echo "Deploying $APP..."
fly deploy -a "$APP" --config "$CONFIG" --remote-only

echo "Running health check..."
sleep 5
curl -sf "https://$APP.fly.dev/health" | jq .

echo "Deploy complete."
```

ROLLBACK:
```bash
# List recent deployments
fly releases -a my-app

# Rollback to previous version
fly deploy -a my-app --image registry.fly.io/my-app:previous-sha
```

Source: fly.io documentation"""
    },

    # ================================================================
    # AI ENGINEERING (8 entries)
    # ================================================================
    {
        "title": "Anthropic API — Best Practices",
        "category": "ai_engineering",
        "content": """Anthropic Claude API patterns for production applications.

CLIENT SETUP:
```python
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Async client
async_client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
```

MESSAGE API:
```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "Analyze this text..."},
    ],
    temperature=0.3,  # lower = more deterministic
)
text = response.content[0].text
```

STREAMING:
```python
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=messages,
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

TOOL USE:
```python
tools = [{
    "name": "search_db",
    "description": "Search the database",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
        },
        "required": ["query"],
    },
}]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    tools=tools,
    messages=messages,
)

# Handle tool use
for block in response.content:
    if block.type == "tool_use":
        result = execute_tool(block.name, block.input)
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": block.id, "content": result}
        ]})
```

COST OPTIMIZATION:
- Use Haiku for extraction/classification ($0.25/MTok in, $1.25/MTok out)
- Use Sonnet for reasoning/generation ($3/MTok in, $15/MTok out)
- Use Opus only for complex reasoning ($15/MTok in, $75/MTok out)
- Cache system prompts (prompt_caching beta)

Source: Anthropic API documentation (https://docs.anthropic.com)"""
    },
    {
        "title": "Prompt Engineering — Production Patterns",
        "category": "ai_engineering",
        "content": """Prompt engineering patterns for reliable LLM outputs.

STRUCTURED OUTPUT:
```python
system = \"\"\"You are a data extraction assistant.
Extract the requested information and respond with ONLY valid JSON.
Do not include markdown code blocks or explanations.\"\"\"

user = \"\"\"Extract entities from this text:
{text}

Respond with this exact JSON structure:
{{"entities": [{{"name": "...", "type": "person|org|location", "context": "..."}}]}}\"\"\"
```

CHAIN OF THOUGHT:
```python
system = \"\"\"Analyze the problem step by step.
1. First, identify the key elements
2. Then, analyze relationships between elements
3. Finally, provide your conclusion

Format:
ANALYSIS: [step by step reasoning]
CONCLUSION: [final answer]\"\"\"
```

FEW-SHOT EXAMPLES:
```python
system = \"\"\"Classify customer messages into categories.

Examples:
Input: "My order hasn't arrived yet" → shipping
Input: "Can I get a refund?" → billing
Input: "The product broke after 2 days" → quality
Input: "How do I change my password?" → account\"\"\"
```

SYSTEM PROMPT STRUCTURE:
1. Role definition (who the AI is)
2. Task description (what to do)
3. Constraints (what NOT to do)
4. Output format (exact structure expected)
5. Examples (2-3 representative cases)

ANTI-PATTERNS:
- Vague instructions ("be helpful")
- No output format specification
- Too many constraints (confuses the model)
- Not testing with edge cases
- Relying on the model to "just know" your format

TEMPERATURE GUIDE:
- 0.0: Deterministic, classification, extraction
- 0.3: Analytical, reasoning tasks
- 0.7: Creative writing, brainstorming
- 1.0: Maximum creativity/randomness

Source: Anthropic Prompt Engineering Guide + OpenAI Cookbook"""
    },
    {
        "title": "LLM-Powered Agent Architecture — ReAct Pattern",
        "category": "ai_engineering",
        "content": """ReAct (Reasoning + Acting) pattern for LLM agents.

CORE LOOP:
```python
async def agent_loop(goal: str, tools: list, max_iterations: int = 15):
    messages = [{"role": "user", "content": goal}]

    for i in range(max_iterations):
        response = await llm.create(messages=messages, tools=tools)

        # Check for tool calls
        tool_calls = [b for b in response.content if b.type == "tool_use"]

        if not tool_calls:
            # Agent is done — return final text
            return extract_text(response)

        # Execute tools and feed results back
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tc in tool_calls:
            result = await execute_tool(tc.name, tc.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": str(result),
            })

        messages.append({"role": "user", "content": tool_results})

    return "Max iterations reached"
```

TOOL DESIGN PRINCIPLES:
1. Clear, specific descriptions (the LLM reads them)
2. Granular tools > one god-tool
3. Return structured data, not prose
4. Include error messages that help the LLM self-correct
5. Idempotent where possible

SAFETY GUARDRAILS:
- Max iterations (prevent infinite loops)
- Budget cap (max cost per execution)
- Tool allowlists per phase (read-only during planning)
- Human-in-the-loop for destructive actions

MULTI-AGENT PATTERNS:
- Router: selects which specialist agent handles the task
- Critic: reviews another agent's output
- Executor + Verifier: one acts, one checks

ANTI-PATTERNS:
- No iteration limit (infinite loop risk)
- No cost tracking (surprise bills)
- Giving agent too many tools (decision paralysis)
- Not handling tool errors (agent gets stuck)

Source: ReAct: Synergizing Reasoning and Acting — Yao et al. (2022)"""
    },
    {
        "title": "RAG — Retrieval-Augmented Generation",
        "category": "ai_engineering",
        "content": """RAG patterns for grounding LLM responses in real data.

BASIC RAG PIPELINE:
```
User Query → Embed Query → Vector Search → Retrieve Top-K → Augment Prompt → LLM → Response
```

IMPLEMENTATION:
```python
async def rag_query(question: str, db: asyncpg.Pool, k: int = 5) -> str:
    # 1. Embed the question
    query_embedding = await embed(question)

    # 2. Retrieve relevant documents
    docs = await db.fetch(
        "SELECT content, 1-(embedding <=> $1::vector) as sim "
        "FROM documents ORDER BY embedding <=> $1::vector LIMIT $2",
        str(query_embedding), k
    )

    # 3. Build augmented prompt
    context = "\\n\\n".join(f"[{d['sim']:.2f}] {d['content']}" for d in docs)
    prompt = f\"\"\"Answer based on the following context. If the answer isn't in the context, say so.

Context:
{context}

Question: {question}\"\"\"

    # 4. Generate response
    return await llm.create(messages=[{"role": "user", "content": prompt}])
```

CHUNKING STRATEGIES:
- Fixed size (500-1000 tokens) with overlap (50-100 tokens)
- Semantic chunking (split by topic/section)
- Sentence-level for precise retrieval
- Document-level for broad context

IMPROVING RETRIEVAL:
1. Hybrid search: combine vector + keyword (BM25)
2. Re-ranking: use cross-encoder to re-score top-K
3. Query expansion: rephrase question multiple ways
4. Metadata filtering: pre-filter by date, category, source

EVALUATION METRICS:
- Retrieval: Precision@K, Recall@K, MRR
- Generation: Faithfulness (no hallucination), Relevance, Completeness

ANTI-PATTERNS:
- Chunks too large (dilute relevant info)
- Chunks too small (lose context)
- No overlap between chunks (miss info at boundaries)
- Not evaluating retrieval quality separately from generation

Source: RAG survey papers + Anthropic documentation"""
    },
    {
        "title": "LLM Cost Optimization Strategies",
        "category": "ai_engineering",
        "content": """Strategies to minimize LLM API costs without sacrificing quality.

MODEL TIERING:
```python
TIER_CONFIG = {
    "tier1": "claude-haiku-4-5-20251001",    # $0.25/$1.25 per MTok — fast/cheap
    "tier2": "claude-sonnet-4-20250514",      # $3/$15 per MTok — balanced
    "tier3": "claude-opus-4-20250514",        # $15/$75 per MTok — max quality
}

# Route by task complexity
def select_model(task_type: str) -> str:
    if task_type in ("classify", "extract", "validate"):
        return TIER_CONFIG["tier1"]  # Haiku
    elif task_type in ("analyze", "generate", "code"):
        return TIER_CONFIG["tier2"]  # Sonnet
    elif task_type in ("research", "complex_reasoning"):
        return TIER_CONFIG["tier3"]  # Opus
```

PROMPT CACHING:
```python
# Anthropic prompt caching — cache large system prompts
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=[{
        "type": "text",
        "text": large_system_prompt,
        "cache_control": {"type": "ephemeral"}
    }],
    messages=messages,
)
# Subsequent calls with same system prompt use cache
# Cached input tokens cost 90% less
```

TOKEN OPTIMIZATION:
- Compress context (summarize long documents before sending)
- Remove redundant instructions from system prompt
- Use concise output formats (JSON > prose)
- Set max_tokens appropriately (don't over-allocate)

BUDGET TRACKING:
```python
class Budget:
    def __init__(self, max_cost: float):
        self.max_cost = max_cost
        self.total_cost = 0.0

    def track(self, usage: dict, model: str):
        input_cost = usage["input_tokens"] * MODEL_PRICES[model]["input"]
        output_cost = usage["output_tokens"] * MODEL_PRICES[model]["output"]
        self.total_cost += input_cost + output_cost

    def exceeded(self) -> bool:
        return self.total_cost >= self.max_cost
```

ANTI-PATTERNS:
- Using Opus for everything (10-60x more expensive than Haiku)
- Not tracking costs per request
- Sending full documents when a summary would suffice
- No budget caps (surprise $500 bills)

Source: Anthropic pricing docs + production experience"""
    },
    {
        "title": "LLM Output Parsing and Validation",
        "category": "ai_engineering",
        "content": """Reliable parsing of LLM outputs for production systems.

JSON PARSING WITH FALLBACKS:
```python
import json
import re

def parse_llm_json(text: str) -> dict | None:
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code blocks
    cleaned = re.sub(r'^```(?:json)?\\n?', '', text.strip())
    cleaned = re.sub(r'\\n?```$', '', cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Find JSON in text
    match = re.search(r'\\{[\\s\\S]*\\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None
```

PYDANTIC VALIDATION:
```python
class LLMResponse(BaseModel):
    entities: list[Entity]
    confidence: float = Field(ge=0, le=1)
    reasoning: str

def parse_and_validate(text: str) -> LLMResponse:
    data = parse_llm_json(text)
    if data is None:
        raise ValueError("Could not parse JSON from LLM response")
    return LLMResponse(**data)  # Pydantic validates
```

RETRY ON PARSE FAILURE:
```python
async def get_structured_output(prompt: str, schema: type[BaseModel],
                                 max_retries: int = 2) -> BaseModel:
    for attempt in range(max_retries + 1):
        response = await llm.create(messages=[{"role": "user", "content": prompt}])
        try:
            return parse_and_validate(response.text, schema)
        except (ValueError, ValidationError) as e:
            if attempt < max_retries:
                prompt += f"\\n\\nYour previous response had an error: {e}. Please fix and try again."
            else:
                raise
```

ANTI-PATTERNS:
- Assuming LLM always returns valid JSON
- No retry mechanism for parse failures
- Not validating parsed data against schema
- Regex-only parsing (fragile)

Source: Production experience + Anthropic tool use documentation"""
    },
    {
        "title": "LLM Evaluation and Testing",
        "category": "ai_engineering",
        "content": """Testing and evaluating LLM-powered features.

DETERMINISTIC TESTS (unit-level):
```python
# Test prompt construction
def test_build_analysis_prompt():
    prompt = build_prompt(input="test query", mode="analysis")
    assert "ANALYSIS" in prompt
    assert "test query" in prompt

# Test output parsing
def test_parse_entities():
    raw = '{{"entities": [{{"name": "Alice", "type": "person"}}]}}'
    result = parse_entities(raw)
    assert len(result.entities) == 1
    assert result.entities[0].name == "Alice"

# Test tool execution (mock LLM)
async def test_agent_uses_search_tool(mock_llm):
    mock_llm.return_value = tool_use_response("search_db", {"query": "test"})
    result = await agent_loop("find test data", tools)
    assert mock_llm.call_count >= 1
```

EVALUATION DATASET:
```python
EVAL_CASES = [
    {
        "input": "Mi socio quiere vender su parte",
        "expected_inteligencias": ["INT-07", "INT-06"],
        "min_inteligencias": 3,
        "max_inteligencias": 6,
    },
    # ... 20+ cases
]

async def run_eval():
    results = []
    for case in EVAL_CASES:
        output = await pipeline.execute(case["input"])
        results.append({
            "pass": check_expectations(output, case),
            "cost": output.cost_usd,
            "latency": output.latency_s,
        })
    return aggregate_metrics(results)
```

METRICS:
- Accuracy: % of correct classifications/extractions
- Latency: p50, p90, p99 response times
- Cost: average cost per request
- Consistency: same input → similar output across runs

ANTI-PATTERNS:
- No evaluation dataset (flying blind)
- Testing only happy path
- Evaluating with the same model that generates
- Not tracking metrics over time (regression detection)

Source: Anthropic evaluation guide + ML testing best practices"""
    },
    {
        "title": "Agentic Patterns — Multi-Step Tool Use",
        "category": "ai_engineering",
        "content": """Patterns for building reliable multi-step LLM agents.

PLANNING THEN EXECUTING:
```python
# Phase 1: Plan (read-only tools)
plan = await agent_loop(
    goal=f"Plan how to: {task}",
    tools=READ_ONLY_TOOLS,  # read_file, search, analyze
    max_iterations=5,
)

# Phase 2: Review (separate model validates plan)
review = await review_plan(plan)
if review.verdict != "PASS":
    raise PlanRejected(review.findings)

# Phase 3: Execute (all tools, with budget)
result = await agent_loop(
    goal=f"Execute this plan:\\n{plan}",
    tools=ALL_TOOLS,
    max_iterations=20,
    budget=Budget(max_cost=2.0),
)
```

ERROR RECOVERY:
```python
async def resilient_tool_call(agent, tool_name, args, max_retries=2):
    for attempt in range(max_retries + 1):
        result, is_error = agent.execute(tool_name, args)
        if not is_error:
            return result
        if attempt < max_retries:
            # Feed error back to LLM for self-correction
            agent.add_message("tool_error",
                f"Tool {tool_name} failed: {result}. Try a different approach.")
    return f"FAILED after {max_retries + 1} attempts: {result}"
```

CONTEXT MANAGEMENT:
```python
class ContextManager:
    def maybe_compress(self, history: list, max_tokens: int = 100000) -> list:
        if estimate_tokens(history) < max_tokens:
            return history
        # Keep system prompt + last N messages + summarize middle
        system = history[0]
        recent = history[-10:]
        middle = history[1:-10]
        summary = await summarize(middle)
        return [system, {"role": "user", "content": f"[Summary] {summary}"}] + recent
```

GUARDRAILS:
1. Iteration limit (prevent infinite loops)
2. Cost budget (prevent runaway spending)
3. Tool allowlists per phase
4. Timeout per tool execution
5. Human approval for destructive actions

Source: Anthropic tool use docs + ReAct paper + Code OS v2 architecture"""
    },

    # ================================================================
    # SYSTEMS DESIGN (6 entries)
    # ================================================================
    {
        "title": "Scalability Patterns — Horizontal vs Vertical",
        "category": "systems_design",
        "content": """Scaling strategies for web applications.

VERTICAL SCALING (scale up):
- Bigger machine: more CPU, RAM, faster disk
- Simpler: no distributed systems complexity
- Limited: hardware has ceiling
- When: single-digit TPS, <100GB data, simple architecture

HORIZONTAL SCALING (scale out):
- More machines behind load balancer
- Complex: need stateless services, shared state management
- Unlimited: add machines as needed
- When: >100 TPS, need high availability, microservices

STATELESS SERVICES (prerequisite for horizontal):
```python
# BAD: state in process memory
user_sessions = {}  # lost when process restarts

# GOOD: external state store
async def get_session(session_id: str) -> dict:
    return await redis.get(f"session:{session_id}")
```

CACHING LAYERS:
```
Client → CDN → Reverse Proxy Cache → App Cache (Redis) → Database
```

```python
# Cache-aside pattern
async def get_user(user_id: str) -> User:
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return User.parse_raw(cached)
    user = await db.fetch_user(user_id)
    await redis.setex(f"user:{user_id}", 3600, user.json())
    return user
```

DATABASE SCALING:
- Read replicas for read-heavy workloads
- Sharding for write-heavy workloads
- Connection pooling (PgBouncer) for connection-heavy workloads

ANTI-PATTERNS:
- Premature optimization (scale when needed, not before)
- Sharing state between processes via filesystem
- Not measuring before scaling (profile first)

Source: DDIA — Martin Kleppmann (2017), Chapters 1-2"""
    },
    {
        "title": "Rate Limiting and Backpressure",
        "category": "systems_design",
        "content": """Rate limiting patterns to protect services from overload.

TOKEN BUCKET (most common):
```python
import asyncio
import time

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate          # tokens per second
        self.capacity = capacity  # max burst
        self.tokens = capacity
        self.last_refill = time.monotonic()

    async def acquire(self):
        while True:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            if self.tokens >= 1:
                self.tokens -= 1
                return
            await asyncio.sleep(1 / self.rate)

# Usage: limit to 10 requests/second with burst of 20
limiter = TokenBucket(rate=10, capacity=20)
await limiter.acquire()
result = await call_api()
```

SLIDING WINDOW (Redis-based):
```python
async def is_rate_limited(key: str, limit: int, window_s: int) -> bool:
    now = time.time()
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window_s)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window_s)
    _, _, count, _ = await pipe.execute()
    return count > limit
```

BACKPRESSURE (protect downstream):
```python
# Semaphore limits concurrent calls
sem = asyncio.Semaphore(5)  # max 5 concurrent LLM calls

async def call_llm_with_backpressure(prompt: str) -> str:
    async with sem:
        return await llm.create(prompt)

# Queue with bounded size
work_queue = asyncio.Queue(maxsize=100)
# If queue full, producer blocks → backpressure propagates upstream
```

CIRCUIT BREAKER:
- Closed: normal operation, track failures
- Open: failures exceeded threshold, reject immediately
- Half-open: allow one request to test recovery

ANTI-PATTERNS:
- No rate limiting on external API calls (get banned)
- Unbounded queues (OOM under load)
- Retry without backoff (amplifies load)

Source: DDIA — Kleppmann (2017) + System Design Interview — Alex Xu (2020)"""
    },
    {
        "title": "Distributed Systems — CAP and Consistency",
        "category": "systems_design",
        "content": """CAP theorem and consistency patterns for distributed systems.

CAP THEOREM: In a network partition, choose Consistency or Availability.
- CP: Refuse to serve if can't guarantee consistency (banks)
- AP: Serve potentially stale data but stay available (social media)
- CA: Only possible without network partitions (single node)

CONSISTENCY MODELS:
- Strong: Read always returns latest write (single leader DB)
- Eventual: Reads may be stale but will converge (replicated DBs)
- Causal: Preserves cause-effect ordering (collaboration tools)

PATTERNS:
```python
# Read-after-write consistency
async def create_and_read(data):
    await primary_db.insert(data)        # write to primary
    result = await primary_db.fetch(id)  # read from primary (not replica)
    return result

# Eventual consistency with cache invalidation
async def update_user(user_id, changes):
    await db.update(user_id, changes)
    await cache.delete(f"user:{user_id}")  # invalidate cache
    # Next read will fetch from DB and re-cache
```

IDEMPOTENCY (safe retries):
```python
# Use idempotency key for mutations
@app.post("/orders")
async def create_order(
    request: CreateOrderRequest,
    idempotency_key: str = Header(...),
):
    existing = await db.fetch_by_idempotency_key(idempotency_key)
    if existing:
        return existing  # return cached result
    order = await db.create_order(request, idempotency_key)
    return order
```

ANTI-PATTERNS:
- Assuming network is reliable
- Not handling partial failures
- Two-phase commit across microservices (use saga instead)
- Ignoring clock skew in distributed systems

Source: DDIA — Martin Kleppmann (2017), Chapters 5, 7, 9"""
    },
    {
        "title": "Queue and Worker Patterns",
        "category": "systems_design",
        "content": """Asynchronous processing with queues and workers.

WHEN TO USE QUEUES:
- Long-running tasks (>5s) that shouldn't block API response
- Spike absorption (smooth out traffic bursts)
- Decoupling producers from consumers
- Retry and dead letter handling

SIMPLE IN-PROCESS QUEUE:
```python
import asyncio

class WorkerPool:
    def __init__(self, num_workers: int = 3):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.workers = [asyncio.create_task(self._worker(i))
                       for i in range(num_workers)]

    async def submit(self, task: dict):
        await self.queue.put(task)

    async def _worker(self, worker_id: int):
        while True:
            task = await self.queue.get()
            try:
                await process_task(task)
            except Exception as e:
                logger.error("task_failed", worker=worker_id, error=str(e))
            finally:
                self.queue.task_done()
```

REDIS QUEUE (distributed):
```python
# Producer
await redis.lpush("task_queue", json.dumps(task))

# Consumer
while True:
    _, raw = await redis.brpop("task_queue", timeout=30)
    if raw:
        task = json.loads(raw)
        await process_task(task)
```

DEAD LETTER QUEUE:
```python
async def process_with_retry(task: dict, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await process_task(task)
        except Exception:
            if attempt == max_retries - 1:
                await redis.lpush("dead_letter_queue", json.dumps(task))
                raise
            await asyncio.sleep(2 ** attempt)
```

ANTI-PATTERNS:
- Using database as queue (poor performance, locks)
- Unbounded queue (OOM risk)
- No dead letter queue (tasks silently lost)
- No monitoring of queue depth

Source: DDIA — Kleppmann (2017), Chapter 11"""
    },
    {
        "title": "Load Balancing Strategies",
        "category": "systems_design",
        "content": """Load balancing patterns for distributed applications.

STRATEGIES:
1. Round Robin: Simple, equal distribution. fly.io default.
2. Least Connections: Route to server with fewest active connections.
3. Weighted: Assign weights based on server capacity.
4. IP Hash: Same client always hits same server (session affinity).

FLY.IO LOAD BALANCING:
```toml
[http_service.concurrency]
  type = "requests"      # or "connections"
  hard_limit = 25        # max concurrent per machine
  soft_limit = 20        # start routing to other machines
```

HEALTH CHECKS:
```python
# Active health check — load balancer polls
@app.get("/health")
async def health():
    checks = {"db": "ok", "cache": "ok"}
    try:
        await db_pool.fetchval("SELECT 1")
    except:
        checks["db"] = "error"
    status = 200 if all(v == "ok" for v in checks.values()) else 503
    return JSONResponse(status_code=status, content=checks)
```

GRACEFUL SHUTDOWN:
```python
import signal

async def graceful_shutdown(app):
    # Stop accepting new requests
    # Wait for in-flight requests to complete
    # Close connections
    await app.state.db.close()
    await app.state.http.aclose()

# fly.io sends SIGTERM before stopping
```

AUTO-SCALING TRIGGERS:
- CPU utilization > 70% for 5 minutes
- Request queue depth > threshold
- Response time p95 > SLA threshold
- Custom metrics (active LLM calls > N)

ANTI-PATTERNS:
- Sticky sessions with stateless architecture
- No health checks (routing to dead instances)
- Hard-coded backend addresses
- Not handling graceful shutdown (dropped requests)

Source: fly.io docs + System Design Interview — Alex Xu (2020)"""
    },
    {
        "title": "Data Serialization Formats — JSON, MessagePack, Protobuf",
        "category": "systems_design",
        "content": """Choosing the right serialization format for your use case.

JSON (default choice):
```python
import json
data = json.dumps({"key": "value", "items": [1, 2, 3]})
# Pros: human-readable, universal, great debugging
# Cons: verbose, slow for large payloads, no schema
# Use for: APIs, config files, logging
```

MESSAGEPACK (binary JSON):
```python
import msgpack
data = msgpack.packb({"key": "value", "items": [1, 2, 3]})
# 30-50% smaller than JSON, 2-5x faster
# Pros: compact, fast, JSON-compatible types
# Cons: not human-readable, no schema
# Use for: internal service communication, caching
```

PROTOBUF (schema-enforced):
```protobuf
message User {
  string id = 1;
  string email = 2;
  repeated string tags = 3;
}
```
```python
user = User(id="1", email="a@b.com", tags=["admin"])
data = user.SerializeToString()
# Pros: smallest size, schema evolution, code generation
# Cons: setup overhead, not human-readable
# Use for: high-throughput services, strict contracts
```

COMPARISON:
| Format | Size | Speed | Human-readable | Schema |
|--------|------|-------|----------------|--------|
| JSON | Large | Slow | Yes | No |
| MessagePack | Medium | Fast | No | No |
| Protobuf | Small | Fastest | No | Yes |

DECISION GUIDE:
- External API → JSON (universal)
- Internal high-throughput → MessagePack or Protobuf
- Config/logging → JSON (debuggability)
- Storage → depends on query needs

Source: DDIA — Kleppmann (2017), Chapter 4"""
    },

    # ================================================================
    # CODE QUALITY (5 entries)
    # ================================================================
    {
        "title": "Refactoring — Code Smells and Remedies",
        "category": "code_quality",
        "content": """Common code smells and their refactoring techniques (Martin Fowler).

LONG METHOD → Extract Method:
```python
# Before: 50-line function doing 3 things
def process_order(order):
    # validate... 15 lines
    # calculate total... 20 lines
    # send notification... 15 lines

# After: each step is a clear function
def process_order(order):
    validate_order(order)
    total = calculate_total(order)
    send_order_notification(order, total)
```

FEATURE ENVY → Move Method:
```python
# Before: method uses another object's data extensively
def calculate_shipping(order):
    return order.address.city_rate * order.weight + order.address.tax

# After: move logic to the class that owns the data
class Address:
    def shipping_cost(self, weight: float) -> float:
        return self.city_rate * weight + self.tax
```

PRIMITIVE OBSESSION → Value Object:
```python
# Before: passing raw strings for typed data
def create_user(email: str, phone: str, currency: str): ...

# After: typed value objects
def create_user(email: Email, phone: Phone, currency: Currency): ...
```

LONG PARAMETER LIST → Parameter Object:
```python
# Before
def search(query, page, limit, sort_by, sort_dir, filters, include_archived): ...

# After
@dataclass
class SearchParams:
    query: str
    page: int = 1
    limit: int = 20
    sort_by: str = "created_at"
    sort_dir: str = "desc"
    filters: dict = field(default_factory=dict)
    include_archived: bool = False

def search(params: SearchParams): ...
```

SHOTGUN SURGERY → consolidate related changes in one module.
DIVERGENT CHANGE → split module that changes for multiple reasons.

WHEN NOT TO REFACTOR:
- Code works and won't be touched again
- Before understanding the domain (premature abstraction)
- During a time-critical bugfix

Source: Refactoring — Martin Fowler (2018, 2nd ed.)"""
    },
    {
        "title": "Code Review Best Practices",
        "category": "code_quality",
        "content": """Effective code review for quality and knowledge sharing.

REVIEWER CHECKLIST:
1. Correctness: Does it do what it claims?
2. Security: Any injection, auth bypass, data exposure?
3. Performance: N+1 queries, missing indexes, unbounded loops?
4. Readability: Can I understand it in 5 minutes?
5. Tests: Are edge cases covered?
6. Error handling: What happens when things fail?

GOOD FEEDBACK:
```
# Specific and actionable
"This query will N+1 on the orders table. Consider using a JOIN
or batch fetch. See: orders_repo.py:45 for the existing pattern."

# Not: "This is slow" or "Fix the query"
```

PR SIZE GUIDELINES:
- Ideal: 50-200 lines changed
- Max: 400 lines (beyond this, split the PR)
- Exception: generated code, migrations, large refactors

REVIEW RESPONSE TIME:
- Same-day review for small PRs
- 24h max for standard PRs
- Block time: dedicate 30min/day to reviews

AUTHOR RESPONSIBILITIES:
- Self-review before requesting
- Add context in PR description
- Respond to all comments
- Don't take feedback personally

ANTI-PATTERNS:
- Rubber-stamp approvals (approve without reading)
- Bikeshedding (debating style while ignoring logic bugs)
- Blocking on preferences vs requirements
- Reviewing >500 lines at once (attention drops)

Source: Google Engineering Practices — Code Review Guide"""
    },
    {
        "title": "Technical Debt — Identification and Management",
        "category": "code_quality",
        "content": """Managing technical debt systematically.

TYPES:
1. Deliberate/prudent: "Ship now, refactor next sprint" (known trade-off)
2. Deliberate/reckless: "We don't have time for tests" (dangerous)
3. Inadvertent/prudent: "Now I know how this should have been built" (natural)
4. Inadvertent/reckless: "What's a design pattern?" (skill gap)

IDENTIFICATION:
```python
# Code metrics that signal debt
- Cyclomatic complexity > 10 per function
- File > 500 lines
- Function > 50 lines
- Module with > 20 imports
- Test coverage < 60%
- TODO/FIXME/HACK comments > 10
```

TRACKING:
```markdown
## Tech Debt Register
| ID | Description | Impact | Effort | Priority |
|----|-------------|--------|--------|----------|
| TD-01 | No connection pooling | High (p99 latency) | Medium (2h) | P1 |
| TD-02 | Hardcoded config values | Medium (deploy friction) | Low (1h) | P2 |
| TD-03 | No input validation on /api/execute | High (security) | Low (1h) | P1 |
```

PAYING DOWN DEBT:
- Boy Scout Rule: leave code better than you found it
- 20% rule: dedicate 20% of sprint to debt reduction
- Couple with features: refactor the module you're changing anyway
- Track debt metrics over time

WHEN TO ACCEPT DEBT:
- Validating a product hypothesis (might throw away)
- Time-critical deadline with clear payback plan
- Prototype/MVP that will be rewritten

WHEN TO REFUSE:
- Security vulnerabilities
- Data integrity issues
- Debt that compounds (grows worse over time)

Source: Refactoring — Fowler (2018) + The Pragmatic Programmer — Hunt & Thomas (2019)"""
    },
    {
        "title": "Documentation — What to Document and How",
        "category": "code_quality",
        "content": """Documentation strategy: document the WHY, not the WHAT.

CODE COMMENTS (inline):
```python
# BAD: explains what (redundant with code)
i += 1  # increment i by 1

# GOOD: explains why (non-obvious reason)
i += 1  # skip header row in CSV

# GOOD: explains business rule
if order.total > 10000:
    # Regulatory requirement: orders >10K need manager approval
    await request_approval(order)
```

DOCSTRINGS (module/function level):
```python
def route_to_inteligencias(input_text: str, huecos: list[Hueco]) -> list[str]:
    \"\"\"Select 4-5 inteligencias based on input analysis and detected gaps.

    Uses Sonnet to analyze the input against the Meta-Red framework.
    Enforces Rule 1 (nucleo irreducible) and Rule 3 (sweet spot 4-5).
    \"\"\"
```

README.md (project level):
- What the project does (1-2 sentences)
- How to run it locally
- How to deploy
- Architecture overview (1 diagram)
- Key decisions (link to ADRs)

API DOCUMENTATION:
- FastAPI generates OpenAPI docs automatically
- Add descriptions to routes and models
- Include example requests/responses

WHAT NOT TO DOCUMENT:
- Self-explanatory code
- Implementation details that change frequently
- Anything that can be generated from code
- Comments that restate the code

ANTI-PATTERNS:
- Stale documentation (worse than no documentation)
- Documenting everything equally (document decisions, not boilerplate)
- No README (first thing new devs look for)

Source: The Pragmatic Programmer — Hunt & Thomas (2019)"""
    },
    {
        "title": "Naming Conventions — Clean Code Principles",
        "category": "code_quality",
        "content": """Naming conventions that make code self-documenting.

GENERAL RULES:
- Names reveal intent: `get_active_users()` not `get_data()`
- Avoid abbreviations: `customer` not `cust`, `repository` not `repo`
- Exception: universally known: `db`, `http`, `url`, `id`, `api`

PYTHON CONVENTIONS (PEP 8):
```python
# Variables and functions: snake_case
user_count = 0
def calculate_total(): ...

# Classes: PascalCase
class OrderProcessor: ...

# Constants: UPPER_SNAKE
MAX_RETRIES = 3
DATABASE_URL = "..."

# Private: leading underscore
def _internal_helper(): ...
class _PrivateClass: ...

# "Protected" (convention): single underscore
class Base:
    def _validate(self): ...  # subclasses can override
```

NAMING PATTERNS:
```python
# Boolean: is_, has_, can_, should_
is_active = True
has_permission = check_permission(user)
can_delete = user.role == "admin"

# Functions: verb + noun
def create_user(): ...
def send_notification(): ...
def validate_input(): ...

# Collections: plural
users = []
active_orders = {}

# Factories: create_ or build_
def create_llm_client(): ...
def build_pipeline(): ...
```

ANTI-PATTERNS:
```python
# Too short / meaningless
d = get_data()      # what data?
tmp = process(x)    # what is x?

# Too long / redundant
the_list_of_all_active_user_email_addresses = ...
# Better: active_user_emails = ...

# Misleading
user_list = {}      # it's a dict, not a list!
```

Source: Clean Code — Robert C. Martin (2008), Chapter 2"""
    },
]


def main():
    print(f"Connecting to: {DATABASE_URL.split('@')[0]}@****")
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    conn.autocommit = True

    with conn.cursor() as cur:
        # Add UNIQUE constraint on title if not exists
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'knowledge_base_title_unique'
                ) AND NOT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE indexname = 'knowledge_base_title_unique'
                ) THEN
                    ALTER TABLE knowledge_base
                    ADD CONSTRAINT knowledge_base_title_unique UNIQUE (title);
                END IF;
            END $$;
        """)
        print("UNIQUE constraint on title: OK")

        # Insert entries with ON CONFLICT DO NOTHING
        inserted = 0
        skipped = 0
        for entry in ENTRIES:
            cur.execute("""
                INSERT INTO knowledge_base (title, content, category)
                VALUES (%s, %s, %s)
                ON CONFLICT (title) DO NOTHING
            """, [entry["title"], entry["content"], entry["category"]])
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        # Report
        print(f"\nResults: {inserted} inserted, {skipped} skipped (already existed)")
        print(f"Total entries in script: {len(ENTRIES)}")

        # Verify by category
        cur.execute("""
            SELECT category, count(*) as cnt
            FROM knowledge_base
            GROUP BY category
            ORDER BY category
        """)
        rows = cur.fetchall()
        print("\nKnowledge base by category:")
        total = 0
        for cat, cnt in rows:
            print(f"  {cat}: {cnt}")
            total += cnt
        print(f"  TOTAL: {total}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
