"""
Integration tests for the template loader.

These tests verify that the custom loaders correctly integrate with
Django's template system.
"""

import pytest
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string


@pytest.mark.django_db
class TestLoaderDebugTrue:
    """Tests with DEBUG=True."""

    @pytest.fixture(autouse=True)
    def setup(self, settings):
        settings.DEBUG = True
        # Ensure the feature is enabled
        if hasattr(settings, "RENDER_COMMENTS_ENABLED"):
            del settings.RENDER_COMMENTS_ENABLED

    def test_inline_comment_rendered_as_html(self):
        result = render_to_string("test_templates/inline_comment.html")
        assert "<!--" in result
        assert "{#" not in result
        assert "This is an inline comment" in result
        assert "Another comment" in result

    def test_block_comment_rendered_as_html(self):
        result = render_to_string("test_templates/block_comment.html")
        assert "<!--" in result
        assert "{% comment %}" not in result
        assert "{% endcomment %}" not in result
        assert "This is a block comment" in result
        assert "spanning multiple lines" in result

    def test_mixed_content_template(self):
        result = render_to_string("test_templates/mixed_content.html", {"value": "test_value"})
        # Check variable substitution still works
        assert "test_value" in result
        # Check comments are converted
        assert "<!-- Page title comment -->" in result
        assert "<!-- [section disabled]" in result
        assert "<!-- Debug info -->" in result
        # Check Django tags are stripped (not converted)
        assert "{#" not in result
        assert "{% comment" not in result

    def test_edge_cases_template(self):
        result = render_to_string("test_templates/edge_cases.html")
        # Dashes should be escaped
        assert "- -" in result  # -- becomes - -
        # Unicode should be preserved
        assert "Привет мир" in result
        assert "你好世界" in result
        # Empty comments should work
        assert "<!--  -->" in result

    def test_normal_template_rendering_unaffected(self):
        """Verify that template tags and variables still work."""
        result = render_to_string("test_templates/mixed_content.html", {"value": "hello"})
        assert "hello" in result
        assert "<title>Test Page</title>" in result


@pytest.mark.django_db
class TestLoaderDebugFalse:
    """Tests with DEBUG=False."""

    @pytest.fixture(autouse=True)
    def setup(self, settings):
        settings.DEBUG = False

    def test_inline_comment_stripped(self):
        """Django's normal behavior strips inline comments."""
        result = render_to_string("test_templates/inline_comment.html")
        # Neither HTML nor Django comment syntax should appear
        assert "<!--" not in result or "This is an inline comment" not in result
        assert "{#" not in result

    def test_block_comment_stripped(self):
        """Django's normal behavior strips block comments."""
        result = render_to_string("test_templates/block_comment.html")
        # Block comment content should not appear
        assert "This is a block comment" not in result
        assert "{% comment %}" not in result

    def test_visible_content_preserved(self):
        """Non-comment content should still render."""
        result = render_to_string("test_templates/block_comment.html")
        assert "<p>Visible content</p>" in result


@pytest.mark.django_db
class TestLoaderOptOut:
    """Tests for opt-out functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, settings):
        settings.DEBUG = True
        settings.RENDER_COMMENTS_ENABLED = False

    def test_comments_not_converted_when_disabled(self):
        """When RENDER_COMMENTS_ENABLED=False, comments are stripped normally."""
        result = render_to_string("test_templates/inline_comment.html")
        # Comments should be stripped, not converted to HTML comments
        # The inline comment content should not appear at all
        assert "This is an inline comment" not in result


@pytest.mark.django_db
class TestLoaderErrorHandling:
    """Tests for error handling."""

    def test_missing_template_raises_error(self):
        with pytest.raises(TemplateDoesNotExist):
            render_to_string("nonexistent_template.html")

    def test_missing_template_in_subdir_raises_error(self):
        with pytest.raises(TemplateDoesNotExist):
            render_to_string("test_templates/nonexistent.html")


@pytest.mark.django_db
class TestLoaderIntegration:
    """Integration tests verifying the full template rendering pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self, settings):
        settings.DEBUG = True

    def test_full_html_document(self):
        """Test a complete HTML document template."""
        result = render_to_string("test_templates/mixed_content.html", {"value": "content"})
        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "</html>" in result
        assert "content" in result

    def test_context_variables_work(self):
        """Verify context variable substitution still works."""
        result = render_to_string("test_templates/mixed_content.html", {"value": "my_value"})
        assert "<p>my_value</p>" in result

    def test_template_inheritance_would_work(self):
        """Basic check that templates can be loaded for inheritance."""
        # Just verify we can load templates without error
        result = render_to_string("test_templates/inline_comment.html")
        assert "<div>" in result


@pytest.mark.django_db
class TestHiddenMarker:
    """Tests for hidden comments (!hide marker) in rendered output."""

    @pytest.fixture(autouse=True)
    def setup(self, settings):
        settings.DEBUG = True
        if hasattr(settings, "RENDER_COMMENTS_ENABLED"):
            del settings.RENDER_COMMENTS_ENABLED

    def test_hidden_inline_not_in_output(self):
        """Hidden inline comment should not appear in rendered HTML."""
        result = render_to_string("test_templates/skip_marker.html")
        assert "This should never appear in HTML" not in result
        assert "!hide" not in result

    def test_hidden_block_not_in_output(self):
        """Hidden block comment should not appear in rendered HTML."""
        result = render_to_string("test_templates/skip_marker.html")
        assert "This block should never appear in HTML" not in result

    def test_normal_comments_converted(self):
        """Normal comments should still be converted to HTML comments."""
        result = render_to_string("test_templates/skip_marker.html")
        assert "<!-- This should become an HTML comment -->" in result
        assert "<!-- This block should become an HTML comment -->" in result

    def test_visible_content_preserved(self):
        """Visible content should be preserved."""
        result = render_to_string("test_templates/skip_marker.html")
        assert "<p>Visible content</p>" in result

    def test_hidden_block_with_note_not_in_output(self):
        """Hidden block comment with note should not appear in rendered HTML."""
        result = render_to_string("test_templates/skip_marker.html")
        assert "Block with note also hidden" not in result
        assert "!hide todo" not in result


@pytest.mark.django_db
class TestTemplateTagEscaping:
    """Tests verifying template tags in comments are escaped by default."""

    @pytest.fixture(autouse=True)
    def setup(self, settings):
        settings.DEBUG = True
        if hasattr(settings, "RENDER_COMMENTS_ENABLED"):
            del settings.RENDER_COMMENTS_ENABLED

    def test_template_variable_appears_literally(self):
        """Template variable in comment appears literally, not processed."""
        result = render_to_string(
            "test_templates/template_tags.html",
            {"secret": "TOP_SECRET", "visible_content": "visible"},
        )
        # The {{ secret }} should appear literally in the comment
        assert "{{ secret }}" in result
        # The actual value should NOT appear in the comment
        assert "TOP_SECRET" not in result
        # But regular template rendering still works
        assert "visible" in result

    def test_template_tag_appears_literally(self):
        """Template tag in comment appears literally, not executed."""
        result = render_to_string(
            "test_templates/template_tags.html",
            {"debug": True, "visible_content": "visible"},
        )
        # The {% if debug %} tag should appear literally
        assert "{% if debug %}" in result

    def test_render_marker_processes_variables(self):
        """!render marker allows template variables to be processed."""
        result = render_to_string(
            "test_templates/template_tags.html",
            {"username": "john_doe", "count": 42, "debug_value": "dbg", "visible_content": "x"},
        )
        # !render comments should have processed variables
        assert "user=john_doe" in result
        assert "count=42" in result
        # !render with note should also process and include note
        assert "[debug]" in result
        assert "value=dbg" in result

    def test_render_marker_removes_render_from_output(self):
        """!render marker itself should not appear in final output."""
        result = render_to_string(
            "test_templates/template_tags.html",
            {"username": "test", "count": 1, "debug_value": "test", "visible_content": "x"},
        )
        assert "!render" not in result


@pytest.mark.django_db
class TestHideRenderPrecedence:
    """Tests verifying !hide always takes precedence over !render in rendered output."""

    @pytest.fixture(autouse=True)
    def setup(self, settings):
        settings.DEBUG = True
        if hasattr(settings, "RENDER_COMMENTS_ENABLED"):
            del settings.RENDER_COMMENTS_ENABLED

    def test_hide_render_combination_not_in_output(self):
        """Comments with both !hide and !render should not appear in output."""
        result = render_to_string(
            "test_templates/hide_render_precedence.html",
            {"secret": "TOP_SECRET", "visible": "shown"},
        )
        # The secret value should never appear
        assert "TOP_SECRET" not in result
        # Neither should the markers
        assert "!hide" not in result
        assert "!render" not in result
        # But visible content should render
        assert "shown" in result

    def test_hide_render_no_html_comments_for_hidden(self):
        """Hidden comments should not produce HTML comments regardless of !render."""
        result = render_to_string(
            "test_templates/hide_render_precedence.html",
            {"secret": "TOP_SECRET", "visible": "shown"},
        )
        # Should only have the visible paragraph, no HTML comments with secret
        assert result.count("<!--") == 0  # No HTML comments from hidden content
        assert "<p>shown</p>" in result


class RealisticPageContext:
    """Shared context for realistic page tests."""

    @staticmethod
    def get_context():
        return {
            "page_title": "Test Page Title",
            "site_name": "Test Site",
            "nav_items": [
                {"url": "/home", "label": "Home"},
                {"url": "/about", "label": "About"},
                {"url": "/contact", "label": "Contact"},
            ],
            "user": {
                "is_authenticated": True,
                "username": "testuser",
                "display_name": "Test User",
            },
            "products": [
                {"name": "Widget", "price": "19.99", "on_sale": False},
                {"name": "Gadget", "price": "29.99", "on_sale": True, "sale_price": "24.99"},
                {"name": "Gizmo", "price": "39.99", "on_sale": False},
            ],
            "stats": {"count": 42, "last_updated": "2026-01-15"},
            "current_year": 2026,
        }


@pytest.mark.django_db
class TestRealisticPageDebugTrue:
    """Integration tests for realistic page with DEBUG=True."""

    @pytest.fixture(autouse=True)
    def setup(self, settings):
        settings.DEBUG = True
        if hasattr(settings, "RENDER_COMMENTS_ENABLED"):
            del settings.RENDER_COMMENTS_ENABLED

    def test_page_renders_without_error(self):
        """Page should render successfully with all context variables."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "<!DOCTYPE html>" in result
        assert "</html>" in result

    def test_template_variables_rendered(self):
        """Django template variables outside comments should be processed."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "<title>Test Page Title</title>" in result
        assert "<h1>Test Site</h1>" in result
        assert "Welcome, Test User!" in result
        assert "Total items: 42" in result

    def test_for_loop_renders_items(self):
        """For loops should render all items."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        # Navigation items
        assert 'href="/home"' in result
        assert 'href="/about"' in result
        assert 'href="/contact"' in result
        # Products
        assert "Widget" in result
        assert "Gadget" in result
        assert "Gizmo" in result
        assert "$19.99" in result

    def test_if_condition_works(self):
        """If conditions should work correctly."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        # User is authenticated, should see user section
        assert "Welcome, Test User!" in result
        assert "Please log in to continue." not in result
        # Sale item should show sale badge
        assert "On Sale!" in result

    def test_normal_comments_converted_to_html(self):
        """Normal comments should become HTML comments."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "<!-- This comment appears in HTML when DEBUG=True -->" in result
        assert "<!-- Navigation comment visible in debug mode -->" in result
        assert "<!-- Block comment without note -->" in result
        assert "<!-- Comment inside loop -->" in result

    def test_block_comments_with_notes_include_note(self):
        """Block comments with notes should include the note in brackets."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "<!-- [user section]" in result
        assert "<!-- [copyright]" in result

    def test_hidden_comments_not_in_output(self):
        """Comments with !hide should not appear in output."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "always stripped from output" not in result
        assert "always stripped even with eval" not in result
        assert "Hidden despite eval marker" not in result
        assert "Also hidden despite eval" not in result
        assert "Hidden footer note" not in result
        assert "!hide" not in result

    def test_eval_comments_process_variables(self):
        """Comments with !render should have variables processed."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        # !render comments should show actual values
        assert "<!-- Evaluated comment shows: testuser -->" in result
        assert "<!-- On sale for: $24.99 -->" in result

    def test_escaped_comments_show_literal_tags(self):
        """Normal comments should show template tags literally."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        # The escaped comment should contain the literal {{ stats.count }}
        assert "{{ stats.count }}" in result
        # But outside comments, it should be rendered as 42
        assert "Total items: 42" in result


@pytest.mark.django_db
class TestRealisticPageDebugFalse:
    """Integration tests for realistic page with DEBUG=False."""

    @pytest.fixture(autouse=True)
    def setup(self, settings):
        settings.DEBUG = False
        if hasattr(settings, "RENDER_COMMENTS_ENABLED"):
            del settings.RENDER_COMMENTS_ENABLED

    def test_page_renders_without_error(self):
        """Page should render successfully."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "<!DOCTYPE html>" in result
        assert "</html>" in result

    def test_template_variables_still_work(self):
        """Django template variables should still be processed."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "<title>Test Page Title</title>" in result
        assert "Welcome, Test User!" in result
        assert "Total items: 42" in result

    def test_for_loops_still_work(self):
        """For loops should still render items."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "Widget" in result
        assert "Gadget" in result
        assert "Gizmo" in result

    def test_no_comments_in_output(self):
        """All Django comments should be stripped, none converted to HTML."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        # No comment content should appear
        assert "This comment appears in HTML" not in result
        assert "Navigation comment" not in result
        assert "Block comment with note" not in result
        assert "Block comment without note" not in result
        assert "Comment inside loop" not in result
        assert "Evaluated comment shows" not in result
        assert "always stripped" not in result

    def test_no_html_comment_markers(self):
        """No HTML comment markers from Django comments should appear."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        # Count HTML comments - should be zero from our comments
        # (there might be none, or only if the HTML itself had comments)
        assert "<!-- This comment" not in result
        assert "<!-- Navigation" not in result
        assert "<!-- [user section]" not in result

    def test_no_django_comment_syntax_in_output(self):
        """No Django comment syntax should remain in output."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "{#" not in result
        assert "#}" not in result
        assert "{% comment" not in result
        assert "{% endcomment" not in result


@pytest.mark.django_db
class TestRealisticPageOptOut:
    """Integration tests for realistic page with RENDER_COMMENTS_ENABLED=False."""

    @pytest.fixture(autouse=True)
    def setup(self, settings):
        settings.DEBUG = True
        settings.RENDER_COMMENTS_ENABLED = False

    def test_page_renders_without_error(self):
        """Page should render successfully."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "<!DOCTYPE html>" in result
        assert "</html>" in result

    def test_template_variables_still_work(self):
        """Django template variables should still be processed."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "<title>Test Page Title</title>" in result
        assert "Welcome, Test User!" in result

    def test_comments_stripped_not_converted(self):
        """Comments should be stripped, not converted to HTML comments."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        # Comment content should not appear
        assert "This comment appears in HTML" not in result
        assert "Navigation comment" not in result
        assert "Evaluated comment shows" not in result

    def test_no_html_comment_markers(self):
        """No HTML comment markers from Django comments should appear."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        assert "<!-- This comment" not in result
        assert "<!-- Navigation" not in result
        assert "<!-- [user section]" not in result

    def test_behaves_same_as_debug_false(self):
        """Output should be similar to DEBUG=False."""
        result = render_to_string(
            "test_templates/realistic_page.html",
            RealisticPageContext.get_context(),
        )
        # No Django comment syntax
        assert "{#" not in result
        assert "{% comment" not in result
        # Template logic still works
        assert "Widget" in result
        assert "On Sale!" in result
