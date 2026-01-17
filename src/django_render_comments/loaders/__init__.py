"""
Template loaders that convert Django comments to HTML comments.
"""

from django_render_comments.loaders.app_directories import Loader as AppDirectoriesLoader
from django_render_comments.loaders.filesystem import Loader as FilesystemLoader

__all__ = ["FilesystemLoader", "AppDirectoriesLoader"]
