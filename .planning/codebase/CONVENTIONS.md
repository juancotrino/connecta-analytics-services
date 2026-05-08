# Coding Conventions

**Analysis Date:** 2026-05-07

## Naming Patterns

**Files:**
- Use `snake_case.py` for Python modules and packages across services, for example `services/processing/resources.py`, `services/study_administrator/app/services/study_service.py`, and `services/check_respondent_identity/main.py`.
- Use lowercase package directories with underscores for multiword names, for example `services/check_respondent_identity/` and `services/study_administrator/`.

**Functions:**
- Use `snake_case` for function names and methods, for example `check_health` in `services/storage_proxy/main.py`, `query_filtered_studies` in `services/study_administrator/app/services/study_service.py`, and `eventarc_file_downloader` in `services/processing/event.py`.

**Variables:**
- Use `snake_case` for local and instance variables, for example `study_root_folder_url` in `services/study_administrator/app/services/study_service.py` and `allowed_file_types` in `services/storage_proxy/resources.py`.
- Use `UPPER_SNAKE_CASE` for constants and environment-driven settings, for example `MAX_VERIFICATION_ATTEMPTS` in `services/check_respondent_identity/main.py`, `CODE_EXPIRY_MINUTES` in `services/check_respondent_identity/resources.py`, and `COOKIE_EXPIRY_DAYS` in `services/study_administrator/app/services/auth_service.py`.

**Types:**
- Use `PascalCase` for classes and Pydantic models, for example `StudyService` in `services/study_administrator/app/services/study_service.py`, `BusinessRepository` in `services/study_administrator/app/repositories/business_repository.py`, and `StudyShow` in `services/study_administrator/app/models/study.py`.

## Code Style

**Formatting:**
- Tool used: Not explicitly configured in repository root (no `pyproject.toml`, `setup.cfg`, or `.flake8` detected).
- Follow current in-code style patterns observed in service modules: multi-line calls for long argument lists, f-strings for dynamic messages, and 4-space indentation in files such as `services/study_administrator/app/api/v1/studies.py` and `services/processing/main.py`.

**Linting:**
- Tool used: Not detected as active project configuration.
- Repository hints exist for potential typing/lint workflow in `.gitignore` (for example `.mypy_cache/` in `.gitignore`), but no enforceable lint config file is present at root.

## Import Organization

**Order:**
1. Standard library imports first (for example `os`, `logging`, `datetime`) as in `services/study_administrator/main.py`.
2. Third-party imports second (for example `fastapi`, `pandas`, `firebase_admin`) as in `services/study_administrator/app/services/study_service.py`.
3. Local application imports last (for example `from app.services...`, `from app.repositories...`) as in `services/study_administrator/app/api/v1/business.py`.

**Path Aliases:**
- Not used. Use package-relative imports rooted at module package names (for example `from app.models.user import User` in `services/study_administrator/app/dependencies/authentication.py`, and direct local module imports like `import resources` in `services/storage_proxy/main.py`).

## Error Handling

**Patterns:**
- Wrap endpoint logic in `try/except` and convert failures to framework HTTP errors:
  - FastAPI pattern in `services/study_administrator/app/api/v1/studies.py` and `services/storage_proxy/main.py`.
  - Flask tuple response pattern in `services/check_respondent_identity/main.py`.
- Preserve business-rule failures using explicit exception types (`HTTPException`, `PermissionError`, `ValueError`) as shown in `services/study_administrator/app/services/study_service.py` and `services/study_administrator/app/repositories/business_repository.py`.

## Logging

**Framework:** logging (Python standard library)

**Patterns:**
- Initialize logging through `setup_logging()` helper per service (`services/processing/logger.py`, `services/storage_proxy/logger.py`, `services/study_administrator/app/core/logger.py`).
- Use module loggers with `logging.getLogger(__name__)` and structured f-string messages for errors/warnings/info, for example `services/check_respondent_identity/main.py` and `services/study_administrator/app/services/study_service.py`.

## Comments

**When to Comment:**
- Comment on non-obvious behavior, external constraints, and TODO work, such as auth behavior notes in `services/study_administrator/app/dependencies/authentication.py` and implementation TODOs in `services/processing/main.py`.

**JSDoc/TSDoc:**
- Not applicable (Python codebase). Use Python docstrings for endpoint and helper description, as seen in `services/check_respondent_identity/main.py` and `services/processing/event.py`.

## Function Design

**Size:**
- Keep endpoint handlers small and delegate logic to service/repository layers, following `services/study_administrator/app/api/v1/*.py`.
- Complex data processing remains in utility modules/classes (`services/processing/resources.py`) with static methods or helper methods.

**Parameters:**
- Use explicit type annotations, including union types and generics, for function signatures (`services/study_administrator/app/api/v1/studies.py`, `services/storage_proxy/resources.py`).
- Use dependency injection for FastAPI (`Depends`, `Security`) in `services/study_administrator/app/dependencies/*.py` and `services/study_administrator/app/api/v1/*.py`.

**Return Values:**
- Return typed dictionaries or Pydantic models from API handlers in FastAPI (`services/study_administrator/app/api/v1/studies.py`).
- Return Flask `(dict, status_code)` tuples in Flask service handlers (`services/check_respondent_identity/main.py`).

## Module Design

**Exports:**
- Expose dependency provider factory functions (`get_study_service`, `get_auth_service`, `get_business_service`) at module scope for injection, in `services/study_administrator/app/services/*.py`.
- Keep major domain separation by module role: `app/api`, `app/services`, `app/repositories`, `app/models`, and `app/dependencies` under `services/study_administrator/app/`.

**Barrel Files:**
- Minimal use of `__init__.py` marker files only; no broad re-export/barrel pattern detected (examples: `services/study_administrator/app/api/__init__.py`, `services/study_administrator/app/services/__init__.py`).

---

*Convention analysis: 2026-05-07*
