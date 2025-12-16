"""
Django settings module with automatic environment detection.

Automatically selects the appropriate settings based on:
1. DJANGO_ENV environment variable (production, development, test, ci)
2. Running tests (auto-detects `manage.py test` command)
3. Defaults to development settings
"""

import os
import sys


def _is_running_tests() -> bool:
    """Check if Django tests are being run."""
    return 'test' in sys.argv or 'pytest' in sys.modules


def _get_settings_module() -> str:
    """Determine which settings module to use."""
    # Check for explicit environment variable
    django_env = os.environ.get('DJANGO_ENV', '').lower()

    if django_env == 'production':
        return 'mahjong_api.settings.production'
    elif django_env == 'test':
        return 'mahjong_api.settings.test'
    elif django_env == 'ci':
        return 'mahjong_api.settings.ci'
    elif django_env == 'development':
        return 'mahjong_api.settings.development'

    # Auto-detect test environment
    if _is_running_tests():
        return 'mahjong_api.settings.test'

    # Default to development
    return 'mahjong_api.settings.development'


# Import all settings from the appropriate module
_settings_module = _get_settings_module()

if _settings_module == 'mahjong_api.settings.production':
    from .production import *  # noqa: F401, F403
elif _settings_module == 'mahjong_api.settings.test':
    from .test import *  # noqa: F401, F403
elif _settings_module == 'mahjong_api.settings.ci':
    from .ci import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403
