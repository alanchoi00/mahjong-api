from .settings import *  # noqa

DEBUG = True
SECRET_KEY = 'test-secret-key'  # safe dummy key for tests

ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # or str(BASE_DIR / "test_db.sqlite3")
    },
}
# Don't talk to SQS in CI tests
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Eager mode: tasks execute synchronously in the same process
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# No SQS-specific transport options in tests
CELERY_BROKER_TRANSPORT_OPTIONS = {}
CELERY_TASK_DEFAULT_QUEUE = 'test-queue'

# Faster password hashing in tests (optional)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Explicit timezone for consistency
TIME_ZONE = 'UTC'
USE_TZ = True
