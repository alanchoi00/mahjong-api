"""
Test settings for mahjong_api project.

Uses testcontainers for PostgreSQL to match production environment.
Automatically detected when running `python manage.py test`.
"""

import atexit

from testcontainers.postgres import PostgresContainer

from .base import *  # noqa: F401, F403

DEBUG = True

SECRET_KEY = 'test-secret-key-not-for-production'

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = []


# Database - PostgreSQL via testcontainers

_postgres = PostgresContainer('postgres:16-alpine')
_postgres.start()

# Register cleanup on exit
atexit.register(_postgres.stop)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': _postgres.dbname,
        'USER': _postgres.username,
        'PASSWORD': _postgres.password,
        'HOST': _postgres.get_container_host_ip(),
        'PORT': _postgres.get_exposed_port(5432),
    },
}


# Celery - eager mode for synchronous test execution

CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_TRANSPORT_OPTIONS = {}
CELERY_TASK_DEFAULT_QUEUE = 'test-queue'


# Faster password hashing in tests

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]


# AWS S3 settings (test defaults)

AWS_STORAGE_BUCKET_NAME = 'test-bucket'


# ML Model settings (test defaults)

MODEL_DIR = '/ml/models'
MODEL_S3_URI = None
TILE_DETECTOR_MODEL_NAME = 'tile_detector'
TILE_DETECTOR_MODEL_VERSION = 'v0.1.0'
