# Codebase Structure

**Analysis Date:** 2026-05-07

## Directory Layout

```text
connecta-analytics-services/
├── services/                         # Deployable Python application services
│   ├── check_respondent_identity/    # Flask service for respondent verification
│   ├── processing/                   # FastAPI service for Excel/statistical processing
│   ├── storage_proxy/                # FastAPI upload gateway to Cloud Storage
│   └── study_administrator/          # FastAPI service with layered app architecture
├── terraform/                        # IaC for Cloud Run, Storage, Eventarc, IAM
├── .github/workflows/                # CI/CD workflow definitions
├── docs/                             # Service-specific design/refactor docs
├── notebooks/                        # Ad-hoc analysis notebooks
├── .planning/codebase/               # Generated codebase mapping documents
└── README.md                         # Repository summary
```

## Directory Purposes

**`services/`:**
- Purpose: Host all deployable runtime services.
- Contains: Service folders with `main.py`, `requirements.txt`, `Dockerfile`, and service-specific modules.
- Key files: `services/check_respondent_identity/main.py`, `services/processing/main.py`, `services/storage_proxy/main.py`, `services/study_administrator/main.py`.

**`services/check_respondent_identity/`:**
- Purpose: Respondent qualification and phone/WhatsApp code verification API.
- Contains: Flask routes (`main.py`), business/data functions (`resources.py`), logging setup (`logger.py`), static phone-code data (`countries_phone_codes.json`).
- Key files: `services/check_respondent_identity/main.py`, `services/check_respondent_identity/resources.py`.

**`services/processing/`:**
- Purpose: Event-driven and direct statistical processing workflows.
- Contains: FastAPI entrypoint (`main.py`), Eventarc/GCS decorator (`event.py`), heavy Excel processing logic (`resources.py`), transitional stub (`legacy.py`).
- Key files: `services/processing/main.py`, `services/processing/event.py`, `services/processing/resources.py`.

**`services/storage_proxy/`:**
- Purpose: Validate and upload files to service-scoped Cloud Storage buckets.
- Contains: FastAPI entrypoint (`main.py`), Cloud Storage helper functions (`resources.py`), YAML config for file types.
- Key files: `services/storage_proxy/main.py`, `services/storage_proxy/resources.py`, `services/storage_proxy/allowed_file_types.yaml`.

**`services/study_administrator/`:**
- Purpose: Authenticated study management API with data and document workflows.
- Contains: FastAPI entrypoint and layered `app/` package.
- Key files: `services/study_administrator/main.py`, `services/study_administrator/utils/api_versions.py`, `services/study_administrator/app/api/v1/studies.py`.

**`services/study_administrator/app/api/`:**
- Purpose: Versioned API routers.
- Contains: Version package `v1/` and endpoint modules.
- Key files: `services/study_administrator/app/api/v1/auth.py`, `services/study_administrator/app/api/v1/business.py`, `services/study_administrator/app/api/v1/studies.py`.

**`services/study_administrator/app/dependencies/`:**
- Purpose: Security/auth middleware dependencies.
- Contains: Token parsing, JWT validation, role authorization.
- Key files: `services/study_administrator/app/dependencies/authentication.py`, `services/study_administrator/app/dependencies/authorization.py`.

**`services/study_administrator/app/services/`:**
- Purpose: Business logic orchestration layer.
- Contains: Service classes for auth, business metadata, and study workflows.
- Key files: `services/study_administrator/app/services/auth_service.py`, `services/study_administrator/app/services/business_service.py`, `services/study_administrator/app/services/study_service.py`.

**`services/study_administrator/app/repositories/`:**
- Purpose: Data-access integration layer.
- Contains: Firestore/Firebase/BigQuery/SharePoint retrieval and persistence logic.
- Key files: `services/study_administrator/app/repositories/auth_repository.py`, `services/study_administrator/app/repositories/business_repository.py`, `services/study_administrator/app/repositories/study_repository.py`.

**`services/study_administrator/app/core/`:**
- Purpose: Shared external client wrappers and platform primitives.
- Contains: BigQuery wrapper, Firebase singleton, SharePoint adapter, Teams card helpers, logger.
- Key files: `services/study_administrator/app/core/big_query.py`, `services/study_administrator/app/core/firebase.py`, `services/study_administrator/app/core/sharepoint.py`, `services/study_administrator/app/core/teams/webhook.py`.

**`services/study_administrator/app/models/`:**
- Purpose: Typed request/response/domain schemas.
- Contains: Pydantic models and validators.
- Key files: `services/study_administrator/app/models/study.py`, `services/study_administrator/app/models/user.py`, `services/study_administrator/app/models/validators/__init__.py`.

**`terraform/`:**
- Purpose: Provision cloud infrastructure and service deployment resources.
- Contains: Root Terraform composition and custom modules.
- Key files: `terraform/main.tf`, `terraform/provider.tf`, `terraform/variables.tf`, `terraform/modules/cloud_run/main.tf`, `terraform/modules/eventarc/main.tf`, `terraform/modules/service_account/main.tf`.

**`.github/workflows/`:**
- Purpose: Build, push, deploy, and refresh infrastructure via CI/CD.
- Contains: Deployment workflow with change detection and matrix service builds.
- Key files: `.github/workflows/services-deployment.yml`.

**`docs/`:**
- Purpose: Human-readable plans and design notes.
- Contains: Markdown docs by service/topic.
- Key files: `docs/check_respondent_identity/refactor-plan.md`, `docs/check_respondent_identity/consumer-code.md`.

## Key File Locations

**Entry Points:**
- `services/check_respondent_identity/main.py`: Flask app entrypoint for respondent verification flows.
- `services/processing/main.py`: FastAPI app entrypoint for processing/Eventarc endpoints.
- `services/storage_proxy/main.py`: FastAPI upload API entrypoint.
- `services/study_administrator/main.py`: FastAPI app entrypoint with dynamic API version mounting.

**Configuration:**
- `services/*/requirements.txt`: Per-service Python dependency manifests.
- `services/*/Dockerfile`: Per-service container build configuration.
- `services/storage_proxy/allowed_file_types.yaml`: File-extension policy for upload service.
- `terraform/variables.tf`: Infrastructure variable contract.
- `.github/workflows/services-deployment.yml`: Build and deployment orchestration.

**Core Logic:**
- `services/check_respondent_identity/resources.py`: Respondent qualification + Twilio/WhatsApp + BQ/Firestore logic.
- `services/processing/resources.py`: Statistical significance and workbook processing implementation.
- `services/storage_proxy/resources.py`: Bucket resolution, metadata parsing, blob creation.
- `services/study_administrator/app/services/study_service.py`: Primary study workflow orchestration.

**Testing:**
- Not detected: no `tests/` directories, `*.test.py`, or `*.spec.py` files found in repository paths scanned.

## Naming Conventions

**Files:**
- Use snake_case for Python modules and service directories.
  - Example modules: `services/study_administrator/app/services/study_service.py`, `services/processing/event.py`.
  - Example services: `services/check_respondent_identity/`, `services/storage_proxy/`.

**Directories:**
- Use lower_snake_case for deployable service names and nested packages.
  - Example top-level service dirs: `services/study_administrator/`, `services/check_respondent_identity/`.
  - Example nested app dirs: `services/study_administrator/app/repositories/`, `services/study_administrator/app/dependencies/`.

## Where to Add New Code

**New Feature:**
- If feature belongs to an existing service, add endpoint in that service’s API boundary first:
  - Flask route: `services/check_respondent_identity/main.py`
  - FastAPI route: `services/storage_proxy/main.py` or `services/processing/main.py`
  - Versioned study admin route: `services/study_administrator/app/api/v1/<new_router>.py` and ensure auto-discovery via `services/study_administrator/utils/api_versions.py` naming.
- Add business orchestration under:
  - `services/study_administrator/app/services/` for study administrator features.
- Add data-access code under:
  - `services/study_administrator/app/repositories/`.
- Tests: Not applicable in current structure (no existing test harness path detected).

**New Component/Module:**
- Shared external integration wrapper for study administrator:
  - `services/study_administrator/app/core/` (or `services/study_administrator/app/core/teams/` for Teams card primitives).
- Cross-cutting auth logic:
  - `services/study_administrator/app/dependencies/`.
- Data schema/model updates:
  - `services/study_administrator/app/models/`.

**Utilities:**
- Service-specific utility modules should be colocated in the owning service directory (for example, `services/storage_proxy/resources.py`, `services/processing/event.py`).
- Study-administrator utility/bootstrapping helpers go under `services/study_administrator/utils/`.

## Special Directories

**`.planning/codebase/`:**
- Purpose: Generated mapping and planning reference docs.
- Generated: Yes.
- Committed: Yes (intended for planner/executor consumption).

**`terraform/modules/`:**
- Purpose: Reusable Terraform module definitions used by root config.
- Generated: No.
- Committed: Yes.

**`terraform/.terraform/`:**
- Purpose: Terraform provider/module cache and local state artifacts.
- Generated: Yes.
- Committed: Yes (currently present in repository paths).

**`services/*/__pycache__/`:**
- Purpose: Python bytecode cache directories.
- Generated: Yes.
- Committed: Yes (currently present in repository paths).

**`.env` (repo root):**
- Purpose: Environment configuration file present at repository root.
- Generated: No.
- Committed: Present in working tree listing (contents intentionally not read).

---

*Structure analysis: 2026-05-07*
