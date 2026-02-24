# 🎯 DriftGuardAI - Refinement Action Plan
## MLOps Production Readiness Track

**Status:** 66/100 Ready  
**Timeline to Production:** 5-8 weeks  
**Current Phase:** Pre-Deployment Refinement  

---

## CRITICAL REFINEMENTS (WEEK 1) - 🔴 BLOCKING

These MUST be completed before any production deployment.

---

### Refinement #1: Fix CORS Configuration
**Priority:** 🔴 **SECURITY BLOCKER**  
**Effort:** 30 minutes  
**Impact:** CRITICAL - Prevents cross-origin attacks  

**Current Problem:**
```python
# ❌ INSECURE - allows attacks from any domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Solution:**
```python
# ✅ SECURE - whitelist specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com",
        "https://admin.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=False,  # Only allow if truly needed
)
```

**File:** `backend/app/main.py` (Line 15-21)

**Testing:**
```bash
# Test from allowed origin
curl -H "Origin: https://yourdomain.com" \
     -H "Access-Control-Request-Method: GET" \
     http://localhost:8000/

# Should return CORS headers
# Test from disallowed origin
curl -H "Origin: https://evil.com" \
     -H "Access-Control-Request-Method: GET" \
     http://localhost:8000/

# Should NOT return CORS headers
```

**Owner:** Backend Team  
**Target Date:** Day 1  
**Validation:** ✅ CORS header verification

---

### Refinement #2: Implement Rate Limiting
**Priority:** 🔴 **SECURITY BLOCKER**  
**Effort:** 2 hours  
**Impact:** CRITICAL - DDoS protection  

**Current Problem:**
```
❌ No rate limiting
❌ Unlimited API requests per user/IP
❌ System vulnerable to abuse and DoS attacks
```

**Solution:**
```bash
# 1. Add to requirements.txt
slowapi==0.1.9
```

```python
# 2. Update backend/app/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"}
    )

# 3. Apply limits to critical endpoints
@router.post("/auth/login")
@limiter.limit("5/minute")
def login(...):
    pass

@router.post("/models/{id}/deploy")
@limiter.limit("10/minute")
def deploy_model(...):
    pass

@router.get("/dashboard/summary")
@limiter.limit("60/minute")
def dashboard_summary(...):
    pass
```

**Rate Limits to Set:**
| Endpoint | Limit | Reason |
|----------|-------|--------|
| POST /auth/login | 5/min | Brute force protection |
| POST /auth/register | 3/min | Account creation spam |
| POST /models | 20/min | Model creation rate |
| POST /models/{id}/deploy | 10/min | Deployment safety |
| GET /dashboard/* | 60/min | Dashboard polling |
| POST /simulation/* | 30/min | Simulation rate |
| GET /* (default) | 100/min | General API rate |

**Testing:**
```bash
# Test rate limiting
for i in {1..10}; do
  curl http://localhost:8000/auth/login -d '{"email":"test","password":"test"}'
done
# Should see 429 after 5 requests
```

**Owner:** Backend Team  
**Target Date:** Day 1-2  
**Validation:** ✅ Rate limit enforcement test

---

### Refinement #3: Add Structured Logging
**Priority:** 🔴 **COMPLIANCE BLOCKER**  
**Effort:** 3 hours  
**Impact:** CRITICAL - Audit trail & debugging  

**Current Problem:**
```
❌ Logs only to console
❌ No structured format
❌ No persistence
❌ Cannot audit security events
❌ No log rotation
```

**Solution:**
```bash
# 1. Add to requirements.txt
python-json-logger==2.0.7
python-dateutil==2.8.2
```

```python
# 2. Create backend/app/core/logging.py
import logging
import logging.config
from pythonjsonlogger import jsonlogger

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(timestamp)s %(level)s %(name)s %(message)s"
        },
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": "/var/log/driftguard/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "json",
            "filename": "/var/log/driftguard/errors.log",
            "maxBytes": 10485760,
            "backupCount": 20
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file", "error_file"]
    },
    "loggers": {
        "app.api": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)

# 3. Update backend/app/main.py
from app.core.logging import LOGGING_CONFIG
import logging.config

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def startup_event():
    logger.info("Application startup", extra={
        "service": "driftguard",
        "version": "7.0.0"
    })
```

**Log Events to Capture:**
```python
# Authentication events
logger.info("user.login_success", extra={"user_id": user.id, "ip": request.client.host})
logger.warning("user.login_failed", extra={"email": email, "ip": request.client.host})

# Deployment events  
logger.info("model.deployment", extra={
    "model_id": model_id,
    "status": "deployed",
    "override_used": override,
    "deployed_by": user.id
})

# Governance events
logger.info("governance.evaluation", extra={
    "model_id": model_id,
    "result_status": status,
    "risk_score": risk_score
})

# Error events
logger.error("database.query_error", extra={
    "query": "SELECT ...",
    "error": str(e),
    "duration_ms": duration
})
```

**Testing:**
```bash
# Check logs are JSON formatted
tail -f /var/log/driftguard/app.log | jq '.'

# Should parse as valid JSON
```

**Owner:** Backend Team  
**Target Date:** Day 2-3  
**Validation:** ✅ JSON log format verification

---

### Refinement #4: Add Request/Response Logging Middleware
**Priority:** 🔴 **SECURITY BLOCKER**  
**Effort:** 1.5 hours  
**Impact:** CRITICAL - Audit trail for all API calls  

**Current Problem:**
```
❌ No visibility into API calls
❌ Cannot debug production issues
❌ No audit trail for compliance
```

**Solution:**
```python
# Add to backend/app/main.py
import time
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request
    logger.info("api.request_start", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "query": str(request.url.query),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    })
    
    try:
        response = await call_next(request)
    except Exception as e:
        duration = time.time() - start_time
        logger.error("api.request_error", extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "error": str(e),
            "duration_ms": duration * 1000
        })
        raise
    
    # Log response
    duration = time.time() - start_time
    log_level = "warning" if response.status_code >= 400 else "info"
    
    logger.log(
        getattr(logging, log_level.upper()),
        "api.request_complete",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration * 1000,
            "slow": duration > 1.0
        }
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response
```

**Testing:**
```bash
curl http://localhost:8000/models
# Check logs for:
# - api.request_start
# - api.request_complete
# - X-Request-ID header present
```

**Owner:** Backend Team  
**Target Date:** Day 3  
**Validation:** ✅ Request ID tracking test

---

### Refinement #5: Configure Database Connection Pooling
**Priority:** 🔴 **STABILITY BLOCKER**  
**Effort:** 45 minutes  
**Impact:** CRITICAL - Connection exhaustion prevention  

**Current Problem:**
```
❌ Default pool_size=5 (too small)
❌ No query timeout (queries can hang forever)
❌ Connection reuse not optimized
```

**Solution:**
```python
# Update backend/app/database/session.py
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool, QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    # Connection pooling
    poolclass=QueuePool,
    pool_size=20,              # ⬆️ Increased from 5
    max_overflow=40,           # Allow overflow for spikes
    pool_recycle=3600,         # Recycle connections hourly
    pool_pre_ping=True,        # Check connection health
    
    # Connection timeout
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30s query timeout
    }
)

# Add logging for pool events
@event.listens_for(engine, "pool_checkin")
def receive_pool_checkin(dbapi_conn, connection_record):
    logger.debug("Connection returned to pool")

@event.listens_for(engine, "pool_connect")
def receive_pool_connect(dbapi_conn, connection_record):
    logger.debug("New connection created")

@event.listens_for(engine, "pool_checkout")
def receive_pool_checkout(dbapi_conn, connection_record, connection_proxy):
    logger.debug("Connection checked out from pool")
```

**Testing:**
```bash
# Monitor pool with psql
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Should see ~5-25 connections under load
# Should not exceed 60 (pool_size + max_overflow)
```

**Owner:** Backend + DevOps Team  
**Target Date:** Day 3  
**Validation:** ✅ Connection pool monitoring

---

## HIGH PRIORITY REFINEMENTS (WEEK 1) - 🟡 URGENT

### Refinement #6: Implement Prometheus Metrics
**Priority:** 🟡 **HIGH**  
**Effort:** 2.5 hours  
**Impact:** HIGH - Production observability  

**Add to requirements.txt:**
```
prometheus-client==0.19.0
```

**Code:**
```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'app_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'app_request_duration_seconds',
    'API request duration',
    ['endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

# Business metrics
model_deployments = Counter(
    'model_deployments_total',
    'Total model deployments',
    ['status']  # success, failure, override
)

governance_violations = Counter(
    'governance_violations_total',
    'Total governance violations',
    ['type']  # drift, fairness, risk
)

database_connections = Gauge(
    'database_connections_active',
    'Active database connections'
)

# Endpoint
@app.get("/metrics")
def metrics():
    from prometheus_client import generate_latest
    return generate_latest()
```

**Testing:**
```bash
curl http://localhost:8000/metrics
# Should return Prometheus format metrics
```

**Owner:** Backend + DevOps Team  
**Target Date:** Day 4-5  
**Validation:** ✅ Metrics endpoint test

---

### Refinement #7: Integrate Error Tracking (Sentry)
**Priority:** 🟡 **HIGH**  
**Effort:** 1 hour  
**Impact:** HIGH - Production error visibility  

**Add to requirements.txt:**
```
sentry-sdk==1.38.0
```

**Code:**
```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

if settings.ENVIRONMENT == "production":
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration()
        ],
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
        release=settings.VERSION,
        before_send=lambda event, hint: event  # Custom filtering
    )
```

**Add to .env:**
```
SENTRY_DSN=https://[key]@sentry.io/[project_id]
```

**Owner:** DevOps Team  
**Target Date:** Day 5  
**Validation:** ✅ Error capture test

---

### Refinement #8: Add Deployment Audit Trail
**Priority:** 🟡 **HIGH**  
**Effort:** 1 hour  
**Impact:** HIGH - Compliance & governance  

**Create Model:**
```python
# backend/app/models/deployment_history.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from datetime import datetime

class DeploymentHistory(Base):
    __tablename__ = "deployment_history"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("model_registry.id"), nullable=False)
    deployed_at = Column(DateTime, default=datetime.utcnow, index=True)
    deployed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    previous_status = Column(String)
    new_status = Column(String)
    governance_result = Column(JSON)
    override_used = Column(Boolean, default=False)
    override_reason = Column(String, nullable=True)
    notes = Column(String, nullable=True)
```

**Update Deploy Endpoint:**
```python
# Add logging to backend/app/api/governance.py
deployment = DeploymentHistory(
    model_id=model_id,
    deployed_by=current_user.id,
    previous_status=model.status,
    new_status="deployed",
    governance_result=governance_result,
    override_used=override,
    override_reason=justification if override else None
)
db.add(deployment)
db.commit()
```

**Owner:** Backend Team  
**Target Date:** Day 4  
**Validation:** ✅ Deployment tracking test

---

### Refinement #9: Add Model Pagination
**Priority:** 🟡 **HIGH**  
**Effort:** 1.5 hours  
**Impact:** MEDIUM - Scalability  

**Backend Change:**
```python
# backend/app/api/model_registry.py
from fastapi import Query

@router.get("/models")
def list_models(
    skip: int = Query(0, ge=0, description="Skip N records"),
    limit: int = Query(10, ge=1, le=100, description="Limit to N records"),
    db: Session = Depends(get_db)
):
    models = db.query(ModelRegistry)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    total = db.query(func.count(ModelRegistry.id)).scalar()
    
    return {
        "models": models,
        "pagination": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    }
```

**Frontend Change:**
```typescript
// src/pages/DashboardPage.tsx
const [page, setPage] = useState(1);
const pageSize = 10;

const fetchModels = async () => {
    const response = await modelAPI.getModels(
        (page - 1) * pageSize,
        pageSize
    );
    setModels(response.data.models);
    setTotalModels(response.data.pagination.total);
};
```

**Owner:** Frontend + Backend Team  
**Target Date:** Day 5  
**Validation:** ✅ Pagination test with 1000+ models

---

### Refinement #10: Implement Redis Caching
**Priority:** 🟡 **HIGH**  
**Effort:** 2 hours  
**Impact:** MEDIUM - Performance  

**Add to requirements.txt:**
```
redis==5.0.1
```

**Code:**
```python
# backend/app/core/cache.py
import redis
import json
from datetime import timedelta

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5
)

def cache_get(key: str):
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None

def cache_set(key: str, value, ttl_seconds: int = 60):
    try:
        redis_client.setex(
            key,
            ttl_seconds,
            json.dumps(value)
        )
    except Exception as e:
        logger.error(f"Cache set error: {e}")

# Usage in dashboard
@router.get("/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    cache_key = "dashboard:summary"
    cached = cache_get(cache_key)
    
    if cached:
        return cached
    
    data = dashboard_service.get_dashboard_summary(db)
    cache_set(cache_key, data, 60)  # 1 minute TTL
    
    return data
```

**Items to Cache:**
- Dashboard summary: 1 min TTL
- Compliance distribution: 5 min TTL
- Risk trends: 10 min TTL
- Policies: 30 min TTL

**Owner:** Backend Team  
**Target Date:** Week 2 Day 1  
**Validation:** ✅ Cache hit ratio monitoring

---

## Testing & Validation Summary

After completing Critical + High Priority refinements:

| Test Type | Status | Criteria |
|-----------|--------|----------|
| Security Scan | ⏳ Pending | Zero critical vulnerabilities |
| Load Test | ⏳ Pending | 3x peak load, <500ms latency |
| Rate Limiting | ⏳ Pending | 429 errors at defined limits |
| Logging | ⏳ Pending | All events in JSON format |
| Error Tracking | ⏳ Pending | 100% error capture |
| Pagination | ⏳ Pending | Works with 10K+ records |
| Caching | ⏳ Pending | Cache hit rate >80% |

---

## Implementation Checklist

### Week 1 - CRITICAL PHASE
```
Day 1:
  [ ] Fix CORS configuration (30 min)
  [ ] Implement rate limiting (2 hrs)
  
Day 2-3:
  [ ] Add structured logging (3 hrs)
  [ ] Add request/response logging (1.5 hrs)
  [ ] Configure DB connection pooling (45 min)

Day 4-5:
  [ ] Prometheus metrics (2.5 hrs)
  [ ] Sentry integration (1 hr)
  [ ] Deployment audit trail (1 hr)
  [ ] Model pagination (1.5 hrs)
  [ ] Redis caching (2 hrs)

Total Week 1: ~16 hours
```

---

## Sign-Off Criteria

✅ **Ready for Staging Deployment When:**
1. All 🔴 Critical refinements complete
2. Security audit passed
3. Load testing successful (500ms p95)
4. Logging verified (JSON format)
5. Monitoring dashboards active
6. On-call team trained
7. Incident runbook prepared

✅ **Ready for Production When:**
1. 2 weeks stable in staging
2. Zero critical incidents
3. All 🟡 High Priority items complete
4. Backup/restore tested
5. DR plan validated
6. Performance SLAs met

---

## Success Metrics (Post-Deployment)

| Metric | Target | Check Frequency |
|--------|--------|-----------------|
| Uptime | 99.5% | Daily |
| Error Rate | <0.5% | Real-time |
| API Latency (p95) | <500ms | Real-time |
| Dashboard Latency | <300ms | Real-time |
| Security Incidents | 0 | Daily |

---

**Document:** MLOps Refinement Action Plan  
**Last Updated:** February 24, 2026  
**Status:** Ready for Implementation  
**Next Review:** After Week 1 completion

---

**🚀 Ready to begin refinements?**

Start with Refinement #1 (CORS Fix) - takes 30 minutes.
Then proceed with others in priority order.

Each refinement is independent and can be completed in parallel by different team members.

Total estimated time to production readiness: **5-8 weeks**
