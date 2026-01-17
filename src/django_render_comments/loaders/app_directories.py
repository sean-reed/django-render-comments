"""
Loader for templates stored in INSTALLED_APPS packages.

This loader extends the filesystem loader to search for templates in the
'templates' directory of each installed application.
"""

from collections.abc import Sequence
from pathlib import Path

from django.template.utils import get_app_template_dirs

from django_render_comments.loaders.filesystem import Loader as FilesystemLoader


class Loader(FilesystemLoader):
    """
    App directories loader with comment preprocessing.

    Searches for templates in the 'templates' subdirectory of each
    installed application, with the same comment-to-HTML conversion
    behavior as the filesystem loader.
    """

    def get_dirs(self) -> Sequence[Path]:
        """
        Return the template directories from installed apps.

        Returns:
            Paths to 'templates' directories in installed apps.
        """
        return get_app_template_dirs("templates")
