"""
CI settings for mahjong_api project.

Used for CI jobs that don't require Docker (linting, migration checks).
Uses SQLite in-memory database.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

SECRET_KEY = 'ci-secret-key-not-for-production'

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = []


# Database - SQLite in-memory for CI

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}


# Celery - disabled for CI

CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_TRANSPORT_OPTIONS = {}
CELERY_TASK_DEFAULT_QUEUE = 'ci-queue'


# AWS S3 settings (CI defaults)

AWS_STORAGE_BUCKET_NAME = 'ci-bucket'


# ML Model settings (CI defaults)

MODEL_DIR = '/ml/models'
MODEL_S3_URI = None
TILE_DETECTOR_MODEL_NAME = 'tile_detector'
TILE_DETECTOR_MODEL_VERSION = 'v0.1.0'
DETECTION_CONFIDENCE_THRESHOLD = 0.5
