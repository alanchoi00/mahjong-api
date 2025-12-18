import os
import sys
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


def _is_testing() -> bool:
    """Check if running in test mode."""
    return 'test' in sys.argv or 'pytest' in sys.modules


class EnvironmentError(Exception):
    """Raised when required environment variables are missing."""

    pass


def get_required_env(key: str, description: str = None) -> str:
    value = os.getenv(key)
    if not value:
        # In test mode, return a dummy value instead of raising
        if _is_testing():
            return f'test-{key.lower()}'
        desc = description or f"Environment variable '{key}'"
        raise OSError(f'{desc} is required but not set')
    return value


def get_optional_env(key: str, default: str = None) -> str:
    value = os.getenv(key)
    if not value and default is not None:
        logger.warning(
            f"Environment variable '{key}' not set, using default: {default}",
        )
        return default
    return value


# Django settings
DJANGO_SECRET_KEY = get_optional_env('DJANGO_SECRET_KEY', 'dev-secret-key')
DJANGO_DEBUG = get_optional_env('DJANGO_DEBUG', 'True')
DJANGO_ALLOWED_HOSTS = get_optional_env('DJANGO_ALLOWED_HOSTS', '*')
DJANGO_CSRF_TRUSTED_ORIGINS = get_optional_env('DJANGO_CSRF_TRUSTED_ORIGINS')

# Database
DATABASE_URL = get_optional_env('DATABASE_URL')

# AWS settings
AWS_REGION = get_optional_env('AWS_REGION', 'ap-southeast-2')

# Celery settings
CELERY_BROKER_URL = get_optional_env('CELERY_BROKER_URL', 'sqs://')
CELERY_RESULT_BACKEND = get_optional_env('CELERY_RESULT_BACKEND', 'django-db')
CELERY_SQS_QUEUE_URL = get_optional_env('CELERY_SQS_QUEUE_URL')
CELERY_TASK_DEFAULT_QUEUE = get_optional_env(
    'CELERY_TASK_DEFAULT_QUEUE',
    'mahjong-detect-queue',
)
CELERY_VISIBILITY_TIMEOUT = get_optional_env(
    'CELERY_VISIBILITY_TIMEOUT',
    '120',
)

# Model settings
MODEL_DIR = get_optional_env('MODEL_DIR', '/ml/models')
TILE_DETECTOR_MODEL_NAME = get_optional_env(
    'TILE_DETECTOR_MODEL_NAME',
    'tile_detector',
)
TILE_DETECTOR_MODEL_VERSION = get_optional_env(
    'TILE_DETECTOR_MODEL_VERSION',
    'v0.1.0',
)

# AWS S3 credentials
# These are optional - if not set, boto3 will use the ECS task role credentials
# For ECS workers, we prefer task role; for local dev, explicit credentials are fine
AWS_ACCESS_KEY_ID = get_optional_env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = get_optional_env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = get_required_env(
    'AWS_STORAGE_BUCKET_NAME',
    'AWS s3 storage bucket name',
)

# Model S3 download settings (for Celery worker)
MODEL_S3_URI = get_optional_env(
    'MODEL_S3_URI',
    None,
)
