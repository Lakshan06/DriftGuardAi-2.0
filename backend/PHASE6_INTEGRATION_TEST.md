# Phase 6 Integration Test Plan

## Overview
Phase 6 introduces RunAnywhere SDK integration for AI-powered model analysis and intelligence.
This test plan verifies that Phase 6 integrates safely with Phase 5 without breaking existing functionality.

## Architecture

### New Components

1. **backend/app/services/phase6/runanywhere_client.py**
   - Singleton SDK wrapper
   - Three main methods:
     - `generate_explanation()` - Risk decision explanations
     - `forecast_risk()` - Risk trajectory forecasting
     - `generate_compliance_summary()` - Compliance analysis
   - All methods have timeout protection (10s)
   - Graceful fallback to static responses
   - Comprehensive error logging

2. **backend/app/api/phase6.py**
   - Three new REST endpoints
   - Integrates with Phase 5 services only
   - No modifications to Phase 5 models or services
   - Async request handling

3. **Updated backend/app/main.py**
   - Imports phase6 router
   - Registers phase6 endpoints
   - Updated version to 6.0.0

## Test Scenarios

### Scenario 1: SDK Availability Test
**Objective**: Verify SDK initialization and availability handling

**Test Steps**:
1. Import RunAnywhereIntegration
2. Check RUNANYWHERE_AVAILABLE flag
3. Verify singleton pattern works
4. Confirm fallback mechanism is active if SDK unavailable

**Expected Results**:
- Client initializes without crashing
- Available flag correctly reflects SDK status
- Singleton pattern returns same instance

### Scenario 2: Fallback Response Test
**Objective**: Verify fallback responses are valid when SDK unavailable

**Test Steps**:
1. Call generate_explanation() with test data
2. Call forecast_risk() with test data
3. Call generate_compliance_summary() with test data
4. Verify all return valid response structures

**Expected Results**:
- All endpoints return valid JSON responses
- Responses include sdk_available: false when SDK unavailable
- All responses include generated_at timestamp
- Responses follow expected schema

### Scenario 3: API Endpoint Tests

#### Test 3.1: POST /models/{id}/explain-decision
```bash
curl -X POST "http://localhost:8000/models/1/explain-decision?threshold=70.0" \
  -H "Authorization: Bearer <token>"
```

**Expectations**:
- Returns 200 OK with explanation
- Includes model_id, model_name, endpoint
- Contains explanation text and recommendations
- sdk_available flag indicates SDK status

#### Test 3.2: GET /models/{id}/risk-forecast
```bash
curl -X GET "http://localhost:8000/models/1/risk-forecast?limit=50" \
  -H "Authorization: Bearer <token>"
```

**Expectations**:
- Returns 200 OK with forecast
- Includes forecast_horizon (5), forecasted_values array
- Contains confidence score
- sdk_available flag indicates SDK status

#### Test 3.3: GET /models/{id}/compliance-score
```bash
curl -X GET "http://localhost:8000/models/1/compliance-score" \
  -H "Authorization: Bearer <token>"
```

**Expectations**:
- Returns 200 OK with compliance summary
- Includes compliance_checks array
- Contains overall_status
- Includes recommendations
- sdk_available flag indicates SDK status

### Scenario 4: Error Handling Tests

#### Test 4.1: Non-existent Model
**Test**: Call any Phase 6 endpoint with invalid model_id

**Expected Result**: Returns 404 Not Found

#### Test 4.2: Timeout Protection
**Test**: Simulate slow SDK response (if SDK available)

**Expected Result**: Request times out after 10s, returns fallback response

#### Test 4.3: SDK Failure Handling
**Test**: Force SDK error (if SDK available)

**Expected Result**: Graceful fallback, error logged, API continues operating

### Scenario 5: Phase 5 Integration Test
**Objective**: Verify Phase 6 safely uses Phase 5 data

**Test Steps**:
1. Create model via existing endpoint
2. Log predictions to generate drift/risk data
3. Call Phase 6 endpoints
4. Verify Phase 5 data is correctly extracted and used
5. Verify Phase 5 data is not modified

**Expected Results**:
- Phase 6 endpoints use correct Phase 5 data
- Phase 5 models/services unchanged
- No side effects on Phase 5 functionality

### Scenario 6: Authentication & Authorization
**Test Steps**:
1. Call Phase 6 endpoints without authentication
2. Call with expired token
3. Call with valid token

**Expected Results**:
- Unauthenticated requests return 401
- Expired tokens return 401
- Valid tokens pass through
- User info available in endpoints

## Test Implementation

### Manual Testing
```bash
# 1. Start API server
cd backend
python -m uvicorn app.main:app --reload

# 2. Run Phase 6 endpoints (with valid auth token)
# POST /models/1/explain-decision?threshold=70.0
# GET /models/1/risk-forecast?limit=50
# GET /models/1/compliance-score

# 3. Verify Phase 5 endpoints still work
# GET /models
# POST /logs
# GET /models/1/risk
```

## Integration Checklist

- [x] Phase 6 module created without importing Phase 5 core services
- [x] SDK wrapper has timeout protection
- [x] Fallback responses defined and tested
- [x] Three endpoints implemented
- [x] All endpoints require authentication
- [x] All endpoints verify model exists
- [x] Error handling returns appropriate HTTP codes
- [x] No modifications to Phase 5 models
- [x] No modifications to Phase 5 services
- [x] No modifications to authentication/governance
- [x] Comprehensive logging throughout
- [x] SDK availability clearly communicated in responses
- [x] Version updated to 6.0.0

## Deployment Checklist

Before deploying to production:
1. Verify RunAnywhere SDK is installed (pip install runanywhere-sdk)
2. Test all three endpoints with real models
3. Monitor error logs for SDK initialization issues
4. Verify timeout protection works (check logs for timeout messages)
5. Test fallback responses in staging without SDK
6. Verify Phase 5 endpoints still work after Phase 6 deployment
7. Check that authentication still works for Phase 6 endpoints
8. Verify database connections aren't affected
9. Monitor for memory leaks (singleton pattern)
10. Test with multiple concurrent requests to Phase 6 endpoints

## Rollback Plan

If issues arise:
1. Remove phase6 router from main.py
2. Comment out or remove Phase 6 API imports
3. Restart API server
4. Phase 5 functionality remains unaffected

## Success Criteria

Phase 6 integration is successful when:
1. All three new endpoints return 200 OK for valid requests
2. All endpoints handle errors gracefully with appropriate HTTP codes
3. Phase 5 endpoints continue to work without any changes
4. Fallback responses work when SDK unavailable
5. SDK responses work when SDK available
6. Authentication/authorization unchanged
7. No database modifications or schema changes
8. Zero breaking changes to existing API contracts
