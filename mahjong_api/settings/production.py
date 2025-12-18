"""
Production settings for mahjong_api project.
"""

from urllib.parse import urlparse

from .base import *  # noqa: F401, F403
from mahjong_api import env

DEBUG = False

SECRET_KEY = env.DJANGO_SECRET_KEY

ALLOWED_HOSTS = env.DJANGO_ALLOWED_HOSTS.split(',')

CSRF_TRUSTED_ORIGINS = (
    env.DJANGO_CSRF_TRUSTED_ORIGINS.split(',')
    if env.DJANGO_CSRF_TRUSTED_ORIGINS
    else []
)


# Database - PostgreSQL for production

_db_url = urlparse(env.DATABASE_URL)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': (_db_url.path or '').lstrip('/'),
        'USER': _db_url.username or '',
        'PASSWORD': _db_url.password or '',
        'HOST': _db_url.hostname or '',
        'PORT': _db_url.port or 5432,
        'CONN_MAX_AGE': 60,
    },
}


# Celery - production settings

CELERY_BROKER_URL = env.CELERY_BROKER_URL
CELERY_RESULT_BACKEND = env.CELERY_RESULT_BACKEND
CELERY_TASK_DEFAULT_QUEUE = env.CELERY_TASK_DEFAULT_QUEUE

CELERY_BROKER_TRANSPORT_OPTIONS = {
    'region': env.AWS_REGION,
    'visibility_timeout': int(env.CELERY_VISIBILITY_TIMEOUT),
    'polling_interval': 1,
    'predefined_queues': {
        'mahjong-detect-queue': {
            'url': env.CELERY_SQS_QUEUE_URL,
        },
    },
}


# AWS S3 settings

AWS_STORAGE_BUCKET_NAME = env.AWS_STORAGE_BUCKET_NAME


# ML Model settings

MODEL_DIR = env.MODEL_DIR
MODEL_S3_URI = env.MODEL_S3_URI
TILE_DETECTOR_MODEL_NAME = env.TILE_DETECTOR_MODEL_NAME
TILE_DETECTOR_MODEL_VERSION = env.TILE_DETECTOR_MODEL_VERSION
DETECTION_CONFIDENCE_THRESHOLD = float(env.DETECTION_CONFIDENCE_THRESHOLD)
