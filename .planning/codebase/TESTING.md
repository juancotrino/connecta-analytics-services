# Testing Patterns

**Analysis Date:** 2026-05-07

## Test Framework

**Runner:**
- Not detected in repository (no `pytest.ini`, `pyproject.toml`, `tox.ini`, or `setup.cfg` found at `/Users/juan/projects/Connecta/connecta-analytics-services`).
- Config: Not detected.

**Assertion Library:**
- Not detected (no test files matching `test_*.py`, `*_test.py`, or `*test*.py` under `services/`).

**Run Commands:**
```bash
Not applicable (no committed automated test runner configuration detected)
Not applicable (no watch-mode testing tooling detected)
Not applicable (no coverage tooling configuration detected)
```

## Test File Organization

**Location:**
- Not detected. No dedicated test directories or co-located test files were found under `services/`.

**Naming:**
- Not detected. Recommended future pattern should follow Python defaults (`test_*.py`), but current repository state has no test files.

**Structure:**
```
Not detected
```

## Test Structure

**Suite Organization:**
```typescript
Not applicable: no test suites currently exist in this repository.
```

**Patterns:**
- Setup pattern: Not detected.
- Teardown pattern: Not detected.
- Assertion pattern: Not detected.

## Mocking

**Framework:** Not detected

**Patterns:**
```typescript
Not applicable: no mocking patterns found because no test files are present.
```

**What to Mock:**
- For future tests, prioritize mocking external integrations currently invoked directly in runtime code:
  - Firestore and Firebase Admin in `services/study_administrator/app/repositories/auth_repository.py` and `services/study_administrator/app/repositories/business_repository.py`.
  - BigQuery client usage in `services/study_administrator/app/repositories/study_repository.py` and `services/check_respondent_identity/resources.py`.
  - Google Cloud Storage client in `services/storage_proxy/resources.py` and `services/processing/event.py`.
  - Twilio and WhatsApp HTTP requests in `services/check_respondent_identity/resources.py`.

**What NOT to Mock:**
- Keep pure transformation logic unmocked and test it directly:
  - Phone normalization and variants in `services/check_respondent_identity/resources.py` (`transform_phone_number`, `get_wp_phone_variants`).
  - DataFrame and Excel processing in `services/processing/resources.py` (`DataProcessor` static methods).
  - Simple permission filtering helpers in `services/study_administrator/app/services/business_service.py` and role/column filtering in `services/study_administrator/app/services/study_service.py`.

## Fixtures and Factories

**Test Data:**
```typescript
Not detected in repository. No fixture/factory modules are committed.
```

**Location:**
- Not detected.

## Coverage

**Requirements:** None enforced in repository configuration.

**View Coverage:**
```bash
Not applicable (no configured coverage command or tool)
```

## Test Types

**Unit Tests:**
- Not used in current committed codebase (no unit test files detected under `/Users/juan/projects/Connecta/connecta-analytics-services/services`).

**Integration Tests:**
- Not used in current committed codebase. Runtime services integrate with external systems but no integration test harness is present.

**E2E Tests:**
- Not used.

## Common Patterns

**Async Testing:**
```typescript
Not detected.
```

**Error Testing:**
```typescript
Not detected.
```

---

*Testing analysis: 2026-05-07*
