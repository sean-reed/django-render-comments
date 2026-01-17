"""
Custom filesystem template loader that converts Django comments to HTML comments.

When DEBUG=True, this loader transforms:
- Inline comments: {# comment #} -> <!-- comment -->
- Block comments: {% comment %}...{% endcomment %} -> <!-- ... -->

When DEBUG=False, templates are returned unchanged (Django strips comments normally).
"""

from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.filesystem import Loader as FilesystemLoader

from django_render_comments.preprocessor import preprocess_template


class Loader(FilesystemLoader):
    """
    Template loader that converts Django comments to HTML comments in DEBUG mode.

    Inherits from FilesystemLoader to reuse directory traversal and Origin handling.
    Only overrides get_contents() to preprocess the template source.
    """

    def get_contents(self, origin: Origin) -> str:
        """
        Load template contents and optionally convert comments to HTML.

        Args:
            origin: The Origin object pointing to the template file.

        Returns:
            Template source, with comments converted if DEBUG=True.

        Raises:
            TemplateDoesNotExist: If the template file cannot be found.
        """
        try:
            with open(origin.name, encoding=self.engine.file_charset) as fp:
                contents = fp.read()
        except FileNotFoundError as err:
            raise TemplateDoesNotExist(origin) from err

        # Only preprocess when DEBUG is True and feature is enabled
        if getattr(settings, "DEBUG", False):
            if getattr(settings, "RENDER_COMMENTS_ENABLED", True):
                contents = preprocess_template(contents)

        return contents
