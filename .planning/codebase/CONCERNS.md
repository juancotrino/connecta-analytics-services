# Codebase Concerns

**Analysis Date:** 2026-05-07

## Tech Debt

**Monolithic Excel processing module:**
- Issue: Statistical processing logic, workbook formatting, parsing, and transformation are concentrated in one oversized module with tightly coupled classes and utility functions.
- Files: `services/processing/resources.py`
- Impact: Changes are high-risk, debugging is slow, and small fixes require understanding unrelated logic.
- Fix approach: Split `services/processing/resources.py` into focused modules (I/O, transformation, significance math, workbook formatting), then add contract tests per module boundary.

**Repository contract is partially unimplemented:**
- Issue: Repository API includes a declared method with no implementation.
- Files: `services/study_administrator/app/repositories/study_repository.py`
- Impact: Callers can rely on a method that does not work, creating runtime failures when usage expands.
- Fix approach: Implement `get_studies` or remove it from the contract and update service layer usages accordingly.

**Non-transactional update strategy for studies:**
- Issue: Study updates are implemented as delete-then-insert operations.
- Files: `services/study_administrator/app/repositories/study_repository.py`
- Impact: Partial failure between delete and insert can cause data loss and inconsistent reads.
- Fix approach: Replace with an atomic BigQuery MERGE/upsert pattern and add retry-safe idempotency keys for update operations.

## Known Bugs

**Temporary file cleanup can raise secondary errors:**
- Symptoms: Upload/processing requests can fail with cleanup-related exceptions that mask original failures.
- Files: `services/processing/main.py`
- Trigger: Any exception before `temp_output_path` assignment, followed by `finally` cleanup referencing `temp_output_path`.
- Workaround: Ensure `temp_output_path` is initialized before `try` and guard cleanup using `if temp_output_path and os.path.exists(...)`.

**Event decorator awaits a synchronous endpoint handler:**
- Symptoms: EventArc-triggered file processing can fail with coroutine/type errors.
- Files: `services/processing/event.py`, `services/processing/main.py`
- Trigger: `eventarc_file_downloader` does `await func(...)` while `get_from_storage` is declared as synchronous `def`.
- Workaround: Make `get_from_storage` async or remove `await` and normalize handler signatures.

**Single-study fetch constructs model from query job object:**
- Symptoms: Study fetch by ID can return invalid data shape or raise conversion exceptions.
- Files: `services/study_administrator/app/repositories/study_repository.py`
- Trigger: `get_study` uses `StudyShow(**dict(query_job))` instead of extracting a row from query results.
- Workaround: Consume query results explicitly (`list(query_job.result())`) and map the first row to `StudyShow`.

## Security Considerations

**PII exposed in URL paths:**
- Risk: Phone numbers and verification codes are sent through route path parameters, which are commonly logged by proxies, gateways, and access logs.
- Files: `services/check_respondent_identity/main.py`
- Current mitigation: Basic CORS restriction and input sanitation.
- Recommendations: Move phone number/code inputs to JSON body parameters on POST endpoints and redact sensitive fields from logs.

**Over-broad exception handling can leak internals:**
- Risk: Raw exception messages are returned to clients in multiple endpoints, exposing internal details.
- Files: `services/check_respondent_identity/main.py`, `services/storage_proxy/main.py`, `services/processing/main.py`, `services/study_administrator/app/api/v1/studies.py`
- Current mitigation: Generic 500 status handling exists.
- Recommendations: Return stable client-safe error codes/messages and keep stack traces only in structured server logs.

**Unsigned operational boundaries for external HTTP calls:**
- Risk: Outbound calls are made without request timeouts and retry policy hardening.
- Files: `services/check_respondent_identity/resources.py`, `services/study_administrator/app/repositories/business_repository.py`, `services/study_administrator/app/core/teams/webhook.py`
- Current mitigation: Minimal status checks in some callers.
- Recommendations: Add explicit timeouts, retry with backoff for transient errors, and circuit-breaker behavior for repeated failures.

## Performance Bottlenecks

**O(N) directory-wide user lookup for consultant resolution:**
- Problem: User resolution iterates through all Firebase Auth users when mapping consultant names to IDs.
- Files: `services/study_administrator/app/repositories/auth_repository.py`, `services/study_administrator/app/services/study_service.py`
- Cause: `get_user_id_from_name` calls `get_users`, which pages all users each time.
- Improvement path: Cache user directory snapshots by TTL and/or store direct name→UID mapping in Firestore.

**High-memory spreadsheet processing path:**
- Problem: Workbook processing reads full sheets and performs repeated DataFrame transformations in memory.
- Files: `services/processing/resources.py`, `services/processing/main.py`
- Cause: Monolithic in-memory operations (`pd.read_excel(sheet_name=None)`, multi-pass transforms, workbook copy/format loops).
- Improvement path: Stream large sheets where possible, split pipeline stages, and add input size thresholds.

## Fragile Areas

**Study lifecycle orchestration with external side effects:**
- Files: `services/study_administrator/app/services/study_service.py`, `services/study_administrator/app/repositories/business_repository.py`, `services/study_administrator/app/core/sharepoint.py`
- Why fragile: One request may mutate BigQuery data, create SharePoint folders, and send Teams cards; partial failures are not compensated.
- Safe modification: Introduce explicit step orchestration with rollback/compensation strategy and idempotent side-effect guards.
- Test coverage: Not detected for this flow.

**Phone verification branching logic across multiple providers:**
- Files: `services/check_respondent_identity/main.py`, `services/check_respondent_identity/resources.py`
- Why fragile: Verification behavior spans Twilio Verify, WhatsApp Graph API, Firestore code store, and BigQuery qualification checks.
- Safe modification: Isolate provider adapters behind interfaces and add contract tests per adapter.
- Test coverage: Not detected for this flow.

## Scaling Limits

**Synchronous CPU-heavy processing on request path:**
- Current capacity: Bounded by single-request CPU/memory for Cloud Run instance handling workbook transformations.
- Limit: Large `.xlsx` inputs can saturate instance resources and increase latency/timeout risk.
- Scaling path: Offload to async job queue/worker pipeline and return job IDs for polling.

**Cross-service dependence on live external systems per request:**
- Current capacity: Request latency depends on Firebase Auth/Firestore, BigQuery, SharePoint, Twilio, and Teams availability.
- Limit: Throughput degrades with external service latency spikes or outages.
- Scaling path: Add caching, bulkhead isolation, and resilient retry/timeout policies per integration.

## Dependencies at Risk

**Multiple service-specific dependency sets without lockfiles:**
- Risk: Reproducibility drift across environments and inconsistent transitive resolution.
- Impact: Deployment differences and non-deterministic runtime behavior across services.
- Migration plan: Introduce lockfiles per service and standardize dependency resolution in CI.

**Potential packaging drift in processing service requirements:**
- Risk: Duplicate entry (`pandas==2.2.3` appears twice) indicates weak dependency hygiene.
- Impact: Harder maintenance and higher risk of unnoticed manifest mistakes.
- Migration plan: Deduplicate `services/processing/requirements.txt` and enforce manifest linting in CI.

## Missing Critical Features

**End-to-end and regression test suite for production flows:**
- Problem: Core flows (file upload, statistical processing, study update lifecycle, respondent verification) have no detected automated regression coverage.
- Blocks: Safe refactoring, rapid incident recovery, and confidence in release quality.

**Operational safeguards for long-running processing:**
- Problem: No detected queue-based job orchestration, status tracking, or retryable task model for spreadsheet processing.
- Blocks: Reliable scaling for larger files and predictable SLO adherence.

## Test Coverage Gaps

**Repository-wide absence of Python test files:**
- What's not tested: Business logic in `services/processing/`, `services/check_respondent_identity/`, `services/storage_proxy/`, and `services/study_administrator/`.
- Files: `services/processing/main.py`, `services/processing/resources.py`, `services/check_respondent_identity/main.py`, `services/check_respondent_identity/resources.py`, `services/storage_proxy/main.py`, `services/study_administrator/app/services/study_service.py`
- Risk: Regressions in core business workflows can ship undetected.
- Priority: High

**Authentication/authorization behavior lacks dedicated tests:**
- What's not tested: Token decode/expiry behavior, role-based endpoint access mapping, and failure mode handling.
- Files: `services/study_administrator/app/dependencies/authentication.py`, `services/study_administrator/app/dependencies/authorization.py`, `services/study_administrator/app/services/auth_service.py`
- Risk: Access-control bugs can cause privilege escalation or legitimate-user lockout.
- Priority: High

---

*Concerns audit: 2026-05-07*
