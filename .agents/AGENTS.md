# AGENTS.md

This file provides guidance to AI Agents when working with code in this repository.

## Project Overview

Mahjong API is a Django REST Framework backend for a mahjong tile detection application. It uses YOLO (via ultralytics) for ML inference to detect mahjong tiles from images, with Celery for async task processing backed by AWS SQS.

## Commands

```bash
# Package management uses pipenv
pipenv install --dev          # Install dependencies
pipenv shell                  # Activate virtualenv

# Development
pipenv run start              # Run dev server (python manage.py runserver)
pipenv run shell              # Django shell
pipenv run migrate            # Run migrations
pipenv run makemigrations     # Create migrations
pipenv run test               # Run tests (auto-detects test settings)
pipenv run new-app <name>     # Create new Django app

# Linting
pipenv run ruff check .       # Lint code
pipenv run ruff check . --fix # Auto-fix lint issues

# Run a single test
pipenv run python manage.py test <app>.tests.<TestClass>.<test_method>
```

## Architecture

### Django Apps
- **core**: Base models (`TimeStampedModel` with created_at/updated_at) and custom DRF exception handling
- **users**: `Client` model for anonymous app installs (identified by install_id)
- **assets**: Presigned S3 upload flow with upload sessions and polymorphic asset references (`AssetRef` uses GenericForeignKey)
- **hands**: Mahjong hand detection - Celery tasks for running ML inference
- **rules**: Mahjong rule sets (placeholder)

### Key Patterns

**Environment Configuration**: All env vars are centralized in `mahjong_api/env.py` using `get_required_env()` and `get_optional_env()` helpers. Import from there, not `os.getenv()` directly.

**Custom API Exceptions**: Inherit from `core.exceptions.BaseAPIException` (uses attrs). The custom exception handler in `core/exceptions.py` is registered in settings.

**Celery Tasks**: Defined in `<app>/tasks.py`. Uses SQS as broker in production, memory broker in tests. Tasks run with `CELERY_TASK_ALWAYS_EAGER=True` during tests.

**ML Model Loading**: Singleton pattern in `ml/inference/model.py` - YOLO model loaded once per process via `get_model()`.

### Settings Structure

Settings use a modular `mahjong_api/settings/` directory:
- `base.py` - shared configuration
- `development.py` - local dev (DEBUG=True)
- `production.py` - production (DJANGO_ENV=production)
- `test.py` - auto-detected when running `manage.py test`

Settings auto-detection in `__init__.py` selects the appropriate module based on `DJANGO_ENV` or test command detection.

### Database
- PostgreSQL in production and local development (via DATABASE_URL)
- PostgreSQL via testcontainers in tests (matches production environment)

### Testing
Test settings (`mahjong_api/settings/test.py`) are auto-detected and configure:
- PostgreSQL via testcontainers (spins up container automatically)
- Eager Celery execution (`CELERY_TASK_ALWAYS_EAGER=True`)
- Memory-based Celery broker

## Code Style

Configured in `pyproject.toml` using ruff:
- Python 3.12+ target
- 79 char line length (86 before E501 triggers)
- Single quotes
- Uses pycodestyle, pyflakes, and flake8-bugbear rules
