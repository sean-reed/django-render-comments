"""
Django app configuration for django-render-comments.
"""

from django.apps import AppConfig


class DjangoRenderCommentsConfig(AppConfig):
    """
    App configuration for the django-render-comments package.

    This app provides custom template loaders that convert Django template
    comments into HTML comments when DEBUG=True.
    """

    name = "django_render_comments"
    verbose_name = "Django Render Comments"
