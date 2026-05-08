# Technology Stack

**Analysis Date:** 2026-05-07

## Languages

**Primary:**
- Python 3.11.1 (container runtime image) - used by all services in `services/check_respondent_identity/`, `services/storage_proxy/`, `services/processing/`, and `services/study_administrator/` via `services/*/Dockerfile`.

**Secondary:**
- HCL (Terraform) - infrastructure definitions in `terraform/main.tf`, `terraform/provider.tf`, and `terraform/modules/**`.
- YAML - CI/CD pipeline and config in `.github/workflows/services-deployment.yml` and `services/storage_proxy/allowed_file_types.yaml`.

## Runtime

**Environment:**
- Python container runtime: `python:3.11.1-slim` in `services/check_respondent_identity/Dockerfile`, `services/storage_proxy/Dockerfile`, `services/processing/Dockerfile`, and `services/study_administrator/Dockerfile`.
- Cloud runtime target: Google Cloud Run, documented in `README.md` and provisioned in `terraform/modules/cloud_run/main.tf`.

**Package Manager:**
- pip (via `pip install -r requirements.txt`) in all service Dockerfiles under `services/*/Dockerfile`.
- Lockfile: missing (no `poetry.lock`, `Pipfile.lock`, or equivalent detected in repository root and subdirectories).

## Frameworks

**Core:**
- FastAPI 0.115.6 - API services in `services/study_administrator/requirements.txt`, `services/storage_proxy/requirements.txt`, and `services/processing/requirements.txt`; app entrypoints in `services/study_administrator/main.py`, `services/storage_proxy/main.py`, `services/processing/main.py`.
- Flask 3.1.0 - respondent identity service in `services/check_respondent_identity/requirements.txt` and `services/check_respondent_identity/main.py`.

**Testing:**
- Not detected (no `pytest`, `unittest`, `nose`, `tox`, `jest`, or test config files detected in repository scan).

**Build/Dev:**
- Docker - image build runtime from `services/*/Dockerfile` and GitHub Actions build steps in `.github/workflows/services-deployment.yml`.
- GitHub Actions - CI/CD workflow in `.github/workflows/services-deployment.yml`.
- Terraform - infrastructure deployment in `terraform/main.tf`, `terraform/provider.tf`, and `.github/workflows/services-deployment.yml`.
- Uvicorn 0.34.0 - ASGI serving for FastAPI services from `services/study_administrator/requirements.txt`, `services/storage_proxy/requirements.txt`, `services/processing/requirements.txt`.
- Gunicorn 23.0.0 - WSGI serving dependency in `services/check_respondent_identity/requirements.txt`.

## Key Dependencies

**Critical:**
- `google-cloud-bigquery==3.27.0` - analytical storage/query path in `services/check_respondent_identity/resources.py` and `services/study_administrator/app/core/big_query.py`.
- `google-cloud-firestore==2.19.0` and `firebase-admin==6.5.0` - identity/business metadata and auth lookups in `services/check_respondent_identity/resources.py`, `services/study_administrator/app/core/firebase.py`, and `services/study_administrator/app/repositories/*.py`.
- `google-cloud-storage==2.19.0` - file upload/download flow in `services/storage_proxy/resources.py` and `services/processing/event.py`.
- `twilio==9.4.1` - SMS verification flow in `services/check_respondent_identity/resources.py`.
- `Office365-REST-Python-Client==2.5.10` - SharePoint integration in `services/study_administrator/app/core/sharepoint.py`.

**Infrastructure:**
- Terraform Google provider + GCS backend in `terraform/provider.tf`.
- `GoogleCloudPlatform/cloud-run/google` module `~> 0.10.0` in `terraform/modules/cloud_run/main.tf`.
- `terraform-google-modules/cloud-storage/google` module `~> 9.1` in `terraform/main.tf`.
- `terraform-google-modules/service-accounts/google` module `~> 4.0` in `terraform/modules/service_account/main.tf`.

## Configuration

**Environment:**
- Runtime environment is selected by `ENV` in `services/check_respondent_identity/main.py`, `services/study_administrator/main.py`, `services/storage_proxy/main.py`, and `services/processing/main.py`.
- `.env` file is present at repository root (`.env`) and local-only dotenv loading exists in service entrypoints; secret values are not stored in docs.
- Cloud Run secret-to-env injection is defined in `terraform/modules/cloud_run/main.tf` (`env_secret_vars`) and populated per service in `terraform/main.tf` (`secrets` lists).

**Build:**
- Container build configuration in `services/*/Dockerfile`.
- Deployment pipeline in `.github/workflows/services-deployment.yml`.
- Terraform backend/provider and infra topology in `terraform/provider.tf` and `terraform/main.tf`.

## Platform Requirements

**Development:**
- Docker support to build service images from `services/*/Dockerfile`.
- Python 3.11-compatible environment for local runs aligned to Docker base image usage in `services/*/Dockerfile`.
- Access to GCP credentials and service APIs used by code paths in `services/**/resources.py` and `services/study_administrator/app/core/*.py`.

**Production:**
- Google Cloud Run deployment target in `README.md` and `terraform/modules/cloud_run/main.tf`.
- Google Artifact Registry for images in `.github/workflows/services-deployment.yml` and image URIs in `terraform/main.tf`.
- GCS-backed Terraform state backend in `terraform/provider.tf`.

---

*Stack analysis: 2026-05-07*
