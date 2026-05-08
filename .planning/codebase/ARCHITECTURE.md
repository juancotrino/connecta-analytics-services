# Architecture

**Analysis Date:** 2026-05-07

## Pattern Overview

**Overall:** Multi-service architecture (Python monorepo) with service-oriented boundaries and layered architecture inside `study_administrator`.

**Key Characteristics:**
- Each deployable service has its own entrypoint and dependencies under `services/<service_name>/` (for example, `services/storage_proxy/main.py`, `services/processing/main.py`, `services/check_respondent_identity/main.py`, `services/study_administrator/main.py`).
- `services/study_administrator/` follows API → dependencies → services → repositories → core integrations → models layering (for example, `services/study_administrator/app/api/v1/studies.py` calling `services/study_administrator/app/services/study_service.py`).
- Infrastructure and deployment are managed separately through Terraform modules in `terraform/` and GitHub Actions in `.github/workflows/services-deployment.yml`.

## Layers

**API Layer (HTTP endpoints):**
- Purpose: Receive HTTP requests, bind request/response models, and map errors to HTTP responses.
- Location: `services/*/main.py`, `services/study_administrator/app/api/v1/*.py`
- Contains: Flask routes in `services/check_respondent_identity/main.py`; FastAPI routes in `services/storage_proxy/main.py`, `services/processing/main.py`, and versioned routers in `services/study_administrator/app/api/v1/`.
- Depends on: Service/business functions in local `resources.py` or application services (`app.services.*`).
- Used by: External clients, Eventarc-triggered requests (`services/processing/event.py`), and frontend consumers.

**Dependency/Security Layer (`study_administrator`):**
- Purpose: Authentication and authorization for protected endpoints.
- Location: `services/study_administrator/app/dependencies/authentication.py`, `services/study_administrator/app/dependencies/authorization.py`
- Contains: Firebase token verification (`get_firebase_user_from_token`), custom JWT decoding (`get_user`), role checks (`authorize`).
- Depends on: `services/study_administrator/app/services/auth_service.py`, `services/study_administrator/app/services/business_service.py`, Firebase Admin SDK.
- Used by: Versioned endpoints in `services/study_administrator/app/api/v1/studies.py` and `services/study_administrator/app/api/v1/business.py`.

**Service Layer (`study_administrator`):**
- Purpose: Business orchestration, policy enforcement, transformations, and workflow coordination.
- Location: `services/study_administrator/app/services/*.py`
- Contains: Study lifecycle orchestration (`study_service.py`), auth token composition (`auth_service.py`), business metadata filtering (`business_service.py`).
- Depends on: Repository layer (`app.repositories.*`) and domain models (`app.models.*`).
- Used by: API routers in `services/study_administrator/app/api/v1/*.py`.

**Repository Layer (`study_administrator`):**
- Purpose: Data access abstraction for BigQuery, Firestore, Firebase Auth, SharePoint-side operations.
- Location: `services/study_administrator/app/repositories/*.py`
- Contains: Query builders and CRUD for studies (`study_repository.py`), role and metadata retrieval (`auth_repository.py`, `business_repository.py`).
- Depends on: Core clients in `services/study_administrator/app/core/`.
- Used by: Service layer (`services/study_administrator/app/services/*.py`).

**Core Integration Layer (`study_administrator`):**
- Purpose: External system clients and reusable integration primitives.
- Location: `services/study_administrator/app/core/*.py`, `services/study_administrator/app/core/teams/*.py`
- Contains: BigQuery client wrapper (`big_query.py`), Firebase initializer (`firebase.py`), SharePoint client (`sharepoint.py`), Teams card/webhook primitives (`teams/*`), logging setup (`logger.py`).
- Depends on: Third-party SDKs (`google-cloud-bigquery`, `firebase-admin`, `Office365-REST-Python-Client`, `requests`).
- Used by: Repository and service layers.

**Domain Model Layer (`study_administrator`):**
- Purpose: Typed data contracts and schema validation.
- Location: `services/study_administrator/app/models/study.py`, `services/study_administrator/app/models/user.py`, `services/study_administrator/app/models/validators/__init__.py`
- Contains: Pydantic models for study payloads and user identity, plus list coercion utility.
- Depends on: Pydantic and typing utilities.
- Used by: API, dependencies, services, repositories.

## Data Flow

**Study Administrator request flow (`/api/v1/studies/*`):**

1. Client calls versioned route mounted by `add_api_versions` in `services/study_administrator/utils/api_versions.py` and `services/study_administrator/main.py`.
2. Router in `services/study_administrator/app/api/v1/studies.py` enforces `Depends(authorize)` / `Depends(get_user)`.
3. `services/study_administrator/app/dependencies/authentication.py` decodes custom JWT; `authorization.py` resolves endpoint role rules from Firestore via `BusinessService`.
4. `services/study_administrator/app/services/study_service.py` runs business logic (role-based column filtering, status checks, folder creation, Teams notifications).
5. `services/study_administrator/app/repositories/study_repository.py` executes BigQuery queries using `services/study_administrator/app/core/big_query.py`.
6. Response model (`StudyShowTotal` or message dict) is returned by router.

**Storage upload to processing flow:**

1. Client uploads file to `POST /upload_file` in `services/storage_proxy/main.py`.
2. `services/storage_proxy/resources.py` validates allowed file extensions from `services/storage_proxy/allowed_file_types.yaml`, writes blob and optional metadata to Cloud Storage bucket.
3. Terraform module `terraform/modules/eventarc/main.tf` provisions Eventarc for service triggers (configured via `terraform/main.tf`).
4. `POST /get_from_storage` in `services/processing/main.py` is wrapped by decorator in `services/processing/event.py`, which extracts object path from Eventarc headers and downloads bytes from Cloud Storage.
5. Processing service decides whether to process based on folder prefix (`landingzone/`) in `services/processing/main.py`.

**Respondent identity and verification flow:**

1. Flask routes in `services/check_respondent_identity/main.py` receive phone/project verification or code requests.
2. Utility logic in `services/check_respondent_identity/resources.py` normalizes phone data and calls Twilio Verify / WhatsApp Graph API.
3. Respondent history and verification state are read/written through BigQuery and Firestore in `services/check_respondent_identity/resources.py`.
4. Route handlers return qualification/auth status and persist respondent tracking data through `write_to_bq`.

**State Management:**
- Request-scoped in-memory state in FastAPI/Flask handlers.
- Persistent state externalized to BigQuery (`services/study_administrator/app/repositories/study_repository.py`, `services/check_respondent_identity/resources.py`), Firestore (`services/study_administrator/app/repositories/auth_repository.py`, `services/study_administrator/app/repositories/business_repository.py`, `services/check_respondent_identity/resources.py`), SharePoint (`services/study_administrator/app/core/sharepoint.py`), and Cloud Storage (`services/storage_proxy/resources.py`, `services/processing/event.py`).

## Key Abstractions

**Dynamic API Version Mounting:**
- Purpose: Auto-discover API versions and routers without hardcoding imports in `main.py`.
- Examples: `services/study_administrator/utils/api_versions.py`, `services/study_administrator/app/api/v1/studies.py`
- Pattern: Filesystem discovery + `importlib.import_module` + `app.mount("/api/{version}", version_app)`.

**Repository Abstraction for External Data:**
- Purpose: Keep query and external system mechanics out of routers.
- Examples: `services/study_administrator/app/repositories/study_repository.py`, `services/study_administrator/app/repositories/business_repository.py`, `services/study_administrator/app/repositories/auth_repository.py`
- Pattern: Service layer orchestrates, repository layer reads/writes.

**Client Wrapper Abstraction:**
- Purpose: Encapsulate provider-specific behaviors.
- Examples: `services/study_administrator/app/core/big_query.py`, `services/study_administrator/app/core/sharepoint.py`, `services/study_administrator/app/core/teams/webhook.py`
- Pattern: Thin wrapper classes with helper methods and retry/error handling.

**Decorator-based Event Download:**
- Purpose: Isolate Eventarc header parsing and GCS download from endpoint body.
- Examples: `services/processing/event.py`, `services/processing/main.py`
- Pattern: Decorator injects `file_name` and `file_content` into route handler.

## Entry Points

**Check Respondent Identity Service:**
- Location: `services/check_respondent_identity/main.py`
- Triggers: HTTP requests to Flask routes.
- Responsibilities: Qualification checks, Twilio/WhatsApp verification, respondent writes to BigQuery.

**Storage Proxy Service:**
- Location: `services/storage_proxy/main.py`
- Triggers: HTTP multipart upload requests.
- Responsibilities: File-type validation and Cloud Storage upload/metadata persistence.

**Processing Service:**
- Location: `services/processing/main.py`
- Triggers: Eventarc-triggered POST and direct processing endpoint calls.
- Responsibilities: Download and route input files, run statistical-processing workflow through `services/processing/resources.py`.

**Study Administrator Service:**
- Location: `services/study_administrator/main.py`
- Triggers: HTTP requests to mounted versioned APIs.
- Responsibilities: Authenticated study and business operations, file workflow to SharePoint, notifications to Teams.

**Infrastructure/Deployment Entry Points:**
- Location: `terraform/main.tf`, `.github/workflows/services-deployment.yml`
- Triggers: GitHub push/workflow_dispatch and Terraform apply.
- Responsibilities: Provision Cloud Run, service accounts, storage, Eventarc, and deploy service images.

## Error Handling

**Strategy:** Endpoint boundary catches exceptions, logs message, and returns/raises HTTP errors.

**Patterns:**
- FastAPI services raise `HTTPException` with explicit status and detail in `services/storage_proxy/main.py`, `services/processing/main.py`, `services/study_administrator/app/api/v1/*.py`.
- `study_administrator` routers catch `HTTPException` separately and re-raise, then map unknown exceptions to `500` (`services/study_administrator/app/api/v1/studies.py`).
- Flask service in `services/check_respondent_identity/main.py` uses `try/except Exception` and returns JSON error messages.
- BigQuery wrapper retries on rate-limit string matching in `services/study_administrator/app/core/big_query.py`.

## Cross-Cutting Concerns

**Logging:** Standard library logging initialization per service (`services/check_respondent_identity/logger.py`, `services/processing/logger.py`, `services/storage_proxy/logger.py`, `services/study_administrator/app/core/logger.py`) with module-level loggers.

**Validation:**
- Request schema validation through Pydantic models in `services/study_administrator/app/models/study.py` and FastAPI parameter typing in `services/storage_proxy/main.py` / `services/processing/main.py`.
- Additional runtime checks for file extensions and authorization in service methods.

**Authentication:**
- Firebase ID token verification and custom JWT issuance/decoding in `services/study_administrator/app/dependencies/authentication.py` and `services/study_administrator/app/services/auth_service.py`.
- Role authorization resolved from Firestore endpoint metadata via `services/study_administrator/app/dependencies/authorization.py`.

---

*Architecture analysis: 2026-05-07*
