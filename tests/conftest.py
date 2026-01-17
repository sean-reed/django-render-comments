"""
pytest configuration and fixtures for django-render-comments tests.
"""

import pytest


@pytest.fixture
def debug_enabled(settings):
    """Enable DEBUG mode for a test."""
    settings.DEBUG = True
    yield
    settings.DEBUG = False


@pytest.fixture
def debug_disabled(settings):
    """Ensure DEBUG mode is disabled for a test."""
    settings.DEBUG = False
    yield


@pytest.fixture
def render_comments_disabled(settings):
    """Disable comment rendering even in DEBUG mode."""
    settings.DEBUG = True
    settings.RENDER_COMMENTS_ENABLED = False
    yield
    settings.DEBUG = False
    if hasattr(settings, "RENDER_COMMENTS_ENABLED"):
        del settings.RENDER_COMMENTS_ENABLED
