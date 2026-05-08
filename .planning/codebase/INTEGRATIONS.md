# External Integrations

**Analysis Date:** 2026-05-07

## APIs & External Services

**Google Cloud Platform:**
- BigQuery - respondent history reads/writes and study querying.
  - SDK/Client: `google-cloud-bigquery` in `services/check_respondent_identity/requirements.txt` and `services/study_administrator/requirements.txt`; usage in `services/check_respondent_identity/resources.py` and `services/study_administrator/app/core/big_query.py`.
  - Auth: `GCP_PROJECT_ID` (read in `services/check_respondent_identity/resources.py` and `services/study_administrator/app/core/big_query.py`).
- Firestore - phone verification state and business/auth config documents.
  - SDK/Client: `google-cloud-firestore` in `services/check_respondent_identity/requirements.txt`; `firebase-admin` in `services/study_administrator/requirements.txt`; usage in `services/check_respondent_identity/resources.py` and `services/study_administrator/app/repositories/*.py`.
  - Auth: `GCP_PROJECT_ID` (used by Firebase/Firestore initializers in `services/study_administrator/app/core/firebase.py` and `services/check_respondent_identity/resources.py`).
- Cloud Storage - upload and event-driven processing pipeline.
  - SDK/Client: `google-cloud-storage` in `services/storage_proxy/requirements.txt` and `services/processing/requirements.txt`; usage in `services/storage_proxy/resources.py` and `services/processing/event.py`.
  - Auth: `GCP_PROJECT_ID` (used in `services/storage_proxy/resources.py` and `services/processing/event.py`).

**Messaging & Verification:**
- Twilio Verify - SMS verification for respondents.
  - SDK/Client: `twilio` in `services/check_respondent_identity/requirements.txt`; usage in `services/check_respondent_identity/resources.py`.
  - Auth: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_SERVICE_SID` (referenced in `services/check_respondent_identity/resources.py`).
- WhatsApp Cloud API (Meta Graph API) - WhatsApp template message verification code send.
  - SDK/Client: raw HTTP via `requests` in `services/check_respondent_identity/resources.py`.
  - Auth: `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN` (referenced in `services/check_respondent_identity/resources.py`).

**Microsoft 365:**
- SharePoint - folder/file management for studies and proposals.
  - SDK/Client: `Office365-REST-Python-Client` in `services/study_administrator/requirements.txt`; usage in `services/study_administrator/app/core/sharepoint.py`.
  - Auth: `SITE_URL`, `CLIENT_ID`, `CLIENT_SECRET` (referenced in `services/study_administrator/app/core/sharepoint.py`).
- Microsoft Teams Webhooks - status/file update notifications.
  - SDK/Client: raw HTTP via `requests` in `services/study_administrator/app/core/teams/webhook.py`.
  - Auth: webhook URL env vars such as `MS_TEAMS_WEBHOOK_STUDY_STATUS_UPDATE` and `MS_TEAMS_WEBHOOK_<FILE>_UPDATE` in `services/study_administrator/app/repositories/business_repository.py`.

**Other External HTTP APIs:**
- World Bank API (`api.worldbank.org`) - country metadata fallback/population for business data mapping via `requests` in `services/study_administrator/app/repositories/business_repository.py`.
  - SDK/Client: `requests`.
  - Auth: Not applicable.

## Data Storage

**Databases:**
- Google BigQuery (`survey_history.respondent`, `business_data.study` usage patterns).
  - Connection: `GCP_PROJECT_ID` in `services/check_respondent_identity/resources.py` and `services/study_administrator/app/core/big_query.py`.
  - Client: `google.cloud.bigquery.Client` in `services/check_respondent_identity/resources.py` and `services/study_administrator/app/core/big_query.py`.
- Google Firestore (Firebase Admin + native Firestore client usage).
  - Connection: `GCP_PROJECT_ID` in `services/study_administrator/app/core/firebase.py`.
  - Client: `firestore.Client()` in `services/check_respondent_identity/resources.py` and `firebase_admin.firestore.client()` in `services/study_administrator/app/repositories/*.py`.

**File Storage:**
- Google Cloud Storage buckets provisioned and used per service via `terraform/main.tf` (`module "cloud_storage"`) and runtime access in `services/storage_proxy/resources.py` and `services/processing/event.py`.

**Caching:**
- None detected.

## Authentication & Identity

**Auth Provider:**
- Firebase Authentication for user identity verification in `services/study_administrator/app/dependencies/authentication.py` (`verify_id_token`).
  - Implementation: bearer token verification + custom JWT issuance/validation via `pyjwt` in `services/study_administrator/app/services/auth_service.py`.

## Monitoring & Observability

**Error Tracking:**
- None detected (no Sentry/New Relic/Honeycomb SDK usage found).

**Logs:**
- Python logging with service-specific setup in `services/check_respondent_identity/logger.py`, `services/storage_proxy/logger.py`, `services/processing/logger.py`, and `services/study_administrator/app/core/logger.py`.
- Runtime logs emitted through `logger`/`app.logger` usage in service entrypoints and repositories, for example `services/processing/main.py` and `services/study_administrator/app/repositories/business_repository.py`.

## CI/CD & Deployment

**Hosting:**
- Google Cloud Run services managed by Terraform in `terraform/main.tf` and `terraform/modules/cloud_run/main.tf`.

**CI Pipeline:**
- GitHub Actions workflow in `.github/workflows/services-deployment.yml`.
  - Builds/pushes Docker images to Artifact Registry.
  - Applies Terraform.
  - Updates Cloud Run service images.
  - Runs refresh-only Terraform apply.

## Environment Configuration

**Required env vars:**
- Core platform: `ENV`, `GCP_PROJECT_ID` (used across `services/**/main.py`, `services/storage_proxy/resources.py`, `services/processing/event.py`, `services/study_administrator/app/core/big_query.py`).
- Twilio/WhatsApp: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_SERVICE_SID`, `WHATSAPP_BUSINESS_ACCOUNT_ID`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN` (declared in `terraform/main.tf`, consumed in `services/check_respondent_identity/resources.py`).
- Study administrator integrations: `SITE_URL`, `CLIENT_ID`, `CLIENT_SECRET`, `MS_TEAMS_WEBHOOK_STUDY_STATUS_UPDATE`, `MS_TEAMS_WEBHOOK_FIELD_DELIVERY_UPDATE`, `MS_TEAMS_WEBHOOK_QUESTIONNAIRE_UPDATE`, `COOKIE_KEY`, `ENCODE_ALGORITHM` (declared in `terraform/main.tf`, consumed in `services/study_administrator/app/core/sharepoint.py`, `services/study_administrator/app/repositories/business_repository.py`, `services/study_administrator/app/services/auth_service.py`).
- CI/CD secrets (GitHub Actions): `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`, `APP_SERVICE_ACCOUNT`, `TF_BACKEND_BUCKET`, `TF_BACKEND_PREFIX` in `.github/workflows/services-deployment.yml`.

**Secrets location:**
- Runtime service secrets are injected from Google Secret Manager to Cloud Run env vars via `env_secret_vars` in `terraform/modules/cloud_run/main.tf`.
- CI/CD secrets are stored in GitHub Actions repository secrets referenced in `.github/workflows/services-deployment.yml`.
- `.env` file present at repository root for local environment configuration (`.env`), contents not documented.

## Webhooks & Callbacks

**Incoming:**
- Eventarc-triggered callback to processing service path `/get_from_storage` configured in `terraform/modules/eventarc/main.tf` and implemented in `services/processing/main.py`.

**Outgoing:**
- Microsoft Teams incoming webhook POSTs from `services/study_administrator/app/core/teams/webhook.py`.
- WhatsApp Cloud API POST to Meta Graph endpoint from `services/check_respondent_identity/resources.py`.
- World Bank API GET requests from `services/study_administrator/app/repositories/business_repository.py`.

---

*Integration audit: 2026-05-07*
