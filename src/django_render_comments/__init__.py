"""
django-render-comments: Render Django template comments as HTML comments.

This package provides custom template loaders that convert Django template
comments ({# ... #} and {% comment %}...{% endcomment %}) into HTML comments
(<!-- ... -->) when DEBUG=True, making them visible in browser developer tools.
"""

__version__ = "0.1.0"

default_app_config = "django_render_comments.apps.DjangoRenderCommentsConfig"
