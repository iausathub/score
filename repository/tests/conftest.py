import pytest


@pytest.fixture(scope="function", autouse=True)
def use_locmem_cache_for_tests(settings):
    """
    Use local memory cache for all tests instead of Redis.
    This ensures tests don't require Redis to be running and are isolated.
    """
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    }
