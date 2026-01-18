"""
Unit tests for the template preprocessor.

These tests verify the regex-based comment conversion logic without
requiring Django's template engine.
"""

from django_render_comments.preprocessor import (
    BLOCK_COMMENT_PATTERN,
    INLINE_COMMENT_PATTERN,
    escape_html_comment,
    preprocess_template,
)


class TestEscapeHtmlComment:
    """Tests for HTML comment escaping."""

    def test_no_escaping_needed(self):
        assert escape_html_comment("simple comment") == "simple comment"

    def test_escape_double_dashes(self):
        assert escape_html_comment("foo--bar") == "foo- -bar"

    def test_escape_multiple_double_dashes(self):
        assert escape_html_comment("a--b--c") == "a- -b- -c"

    def test_escape_consecutive_dashes(self):
        assert escape_html_comment("----") == "- -- -"

    def test_single_dash_unchanged(self):
        assert escape_html_comment("a-b-c") == "a-b-c"

    def test_empty_string(self):
        assert escape_html_comment("") == ""


class TestInlineCommentPattern:
    """Tests for the inline comment regex pattern."""

    def test_simple_match(self):
        match = INLINE_COMMENT_PATTERN.search("{# comment #}")
        assert match is not None
        assert match.group(1) == "comment"

    def test_with_whitespace(self):
        match = INLINE_COMMENT_PATTERN.search("{#   spaced   #}")
        assert match is not None
        assert match.group(1) == "spaced"

    def test_no_match_for_block_comment(self):
        match = INLINE_COMMENT_PATTERN.search("{% comment %}")
        assert match is None


class TestBlockCommentPattern:
    """Tests for the block comment regex pattern."""

    def test_simple_match(self):
        match = BLOCK_COMMENT_PATTERN.search("{% comment %}content{% endcomment %}")
        assert match is not None
        assert match.group(1) is None  # No note
        assert match.group(2) == "content"

    def test_with_double_quote_note(self):
        match = BLOCK_COMMENT_PATTERN.search('{% comment "note" %}content{% endcomment %}')
        assert match is not None
        assert match.group(1) == "note"
        assert match.group(2) == "content"

    def test_with_single_quote_note(self):
        match = BLOCK_COMMENT_PATTERN.search("{% comment 'note' %}content{% endcomment %}")
        assert match is not None
        assert match.group(1) == "note"
        assert match.group(2) == "content"

    def test_multiline_content(self):
        source = """{% comment %}
        line 1
        line 2
        {% endcomment %}"""
        match = BLOCK_COMMENT_PATTERN.search(source)
        assert match is not None
        assert "line 1" in match.group(2)
        assert "line 2" in match.group(2)


class TestInlineCommentConversion:
    """Tests for inline comment conversion."""

    def test_simple_inline_comment(self):
        source = "{# This is a comment #}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- This is a comment -->{% endverbatim %}"

    def test_inline_comment_with_whitespace(self):
        source = "{#   spaced comment   #}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- spaced comment -->{% endverbatim %}"

    def test_inline_comment_in_html(self):
        source = "<div>{# hidden #}</div>"
        result = preprocess_template(source)
        assert result == "<div>{% verbatim %}<!-- hidden -->{% endverbatim %}</div>"

    def test_multiple_inline_comments(self):
        source = "{# first #} text {# second #}"
        result = preprocess_template(source)
        assert (
            result == "{% verbatim %}<!-- first -->{% endverbatim %} text {% verbatim %}"
            "<!-- second -->{% endverbatim %}"
        )

    def test_inline_comment_with_special_chars(self):
        source = "{# <script>alert('xss')</script> #}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- <script>alert('xss')</script> -->{% endverbatim %}"

    def test_inline_comment_with_dashes(self):
        source = "{# foo--bar #}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- foo- -bar -->{% endverbatim %}"

    def test_inline_comment_with_template_vars(self):
        """Template variables are wrapped in verbatim so they appear literally."""
        source = "{# {{ variable }} #}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- {{ variable }} -->{% endverbatim %}"


class TestBlockCommentConversion:
    """Tests for block comment conversion."""

    def test_simple_block_comment(self):
        source = "{% comment %}This is commented{% endcomment %}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- This is commented -->{% endverbatim %}"

    def test_multiline_block_comment(self):
        source = """{% comment %}
Line 1
Line 2
Line 3
{% endcomment %}"""
        result = preprocess_template(source)
        assert "{% verbatim %}<!-- Line 1" in result
        assert "Line 2" in result
        assert "Line 3 -->{% endverbatim %}" in result

    def test_block_comment_with_double_quote_note(self):
        source = '{% comment "disabled feature" %}old code{% endcomment %}'
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- [disabled feature] old code -->{% endverbatim %}"

    def test_block_comment_with_single_quote_note(self):
        source = "{% comment 'todo' %}fix this{% endcomment %}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- [todo] fix this -->{% endverbatim %}"

    def test_block_comment_preserves_surrounding_content(self):
        source = "<p>before</p>{% comment %}hidden{% endcomment %}<p>after</p>"
        result = preprocess_template(source)
        assert result == "<p>before</p>{% verbatim %}<!-- hidden -->{% endverbatim %}<p>after</p>"

    def test_block_comment_with_dashes_in_content(self):
        source = "{% comment %}foo--bar{% endcomment %}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- foo- -bar -->{% endverbatim %}"

    def test_block_comment_with_dashes_in_note(self):
        source = '{% comment "note--here" %}content{% endcomment %}'
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- [note- -here] content -->{% endverbatim %}"


class TestNestedComments:
    """Tests for nested comment scenarios."""

    def test_inline_inside_block_comment(self):
        """Inline comments inside block comments are also converted."""
        source = "{% comment %}{# inner #}{% endcomment %}"
        result = preprocess_template(source)
        # Both the block comment and the inline comment inside it get converted
        # This results in nested HTML comments (valid but unusual)
        # The block comment wraps in verbatim, the inner inline also gets processed
        assert (
            result == "{% verbatim %}<!-- {% verbatim %}<!-- inner -->"
            "{% endverbatim %} -->{% endverbatim %}"
        )

    def test_block_comment_cannot_nest(self):
        """Django doesn't support nested block comments - first endcomment closes."""
        source = "{% comment %}outer{% comment %}inner{% endcomment %}{% endcomment %}"
        result = preprocess_template(source)
        # First endcomment closes the block, rest is rendered
        assert "{% verbatim %}<!-- outer{% comment %}inner -->{% endverbatim %}" in result


class TestMixedContent:
    """Tests for templates with mixed content."""

    def test_comments_with_template_tags(self):
        source = "{% if True %}{# debug #}{{ value }}{% endif %}"
        result = preprocess_template(source)
        assert (
            result
            == "{% if True %}{% verbatim %}<!-- debug -->{% endverbatim %}{{ value }}{% endif %}"
        )

    def test_comments_in_attributes(self):
        """Comments inside HTML attributes - unusual but should work."""
        source = '<div class="{# dynamic #}static">'
        result = preprocess_template(source)
        assert result == '<div class="{% verbatim %}<!-- dynamic -->{% endverbatim %}static">'

    def test_no_comments(self):
        """Template without comments should pass through unchanged."""
        source = "<div>{{ variable }}</div>"
        result = preprocess_template(source)
        assert result == source

    def test_html_only(self):
        """Plain HTML without any Django syntax."""
        source = "<html><body><p>Hello</p></body></html>"
        result = preprocess_template(source)
        assert result == source


class TestEdgeCases:
    """Tests for edge cases and potential issues."""

    def test_empty_inline_comment(self):
        source = "{##}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!--  -->{% endverbatim %}"

    def test_empty_block_comment(self):
        source = "{% comment %}{% endcomment %}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!--  -->{% endverbatim %}"

    def test_comment_like_string_in_javascript(self):
        """JavaScript containing comment-like patterns."""
        source = """<script>
var pattern = "{# not a comment #}";
</script>"""
        result = preprocess_template(source)
        # This WILL be converted - documented limitation
        assert "{% verbatim %}<!-- not a comment -->{% endverbatim %}" in result

    def test_comment_in_string_attribute(self):
        """Comment syntax in attribute values - will be converted."""
        source = '<input value="{# placeholder #}">'
        result = preprocess_template(source)
        assert result == '<input value="{% verbatim %}<!-- placeholder -->{% endverbatim %}">'

    def test_unicode_in_comment(self):
        source = "{# Привет мир 你好世界 #}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- Привет мир 你好世界 -->{% endverbatim %}"

    def test_very_long_comment(self):
        long_text = "x" * 10000
        source = f"{{# {long_text} #}}"
        result = preprocess_template(source)
        assert result == f"{{% verbatim %}}<!-- {long_text} -->{{% endverbatim %}}"

    def test_newlines_in_inline_comment(self):
        """Inline comments with newlines (rare but possible)."""
        source = "{# line1\nline2 #}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- line1\nline2 -->{% endverbatim %}"

    def test_multiple_block_comments(self):
        source = "{% comment %}one{% endcomment %}text{% comment %}two{% endcomment %}"
        result = preprocess_template(source)
        assert (
            result == "{% verbatim %}<!-- one -->{% endverbatim %}text{% verbatim %}"
            "<!-- two -->{% endverbatim %}"
        )

    def test_block_and_inline_comments_mixed(self):
        source = "{# inline #}{% comment %}block{% endcomment %}{# inline2 #}"
        result = preprocess_template(source)
        assert (
            result == "{% verbatim %}<!-- inline -->{% endverbatim %}{% verbatim %}<!-- block -->"
            "{% endverbatim %}{% verbatim %}<!-- inline2 -->{% endverbatim %}"
        )

    def test_whitespace_variations_in_block_tag(self):
        source = "{%  comment  %}content{%  endcomment  %}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- content -->{% endverbatim %}"

    def test_existing_html_comment_unchanged(self):
        source = "<!-- existing html comment -->{# django comment #}"
        result = preprocess_template(source)
        assert (
            result == "<!-- existing html comment -->{% verbatim %}"
            "<!-- django comment -->{% endverbatim %}"
        )


class TestHiddenComments:
    """Tests for hidden comments (!hide marker, skipped, not converted to HTML)."""

    def test_hidden_inline_comment_unchanged(self):
        """Hidden inline comments are left unchanged for Django to strip."""
        source = "{# !hide secret #}"
        result = preprocess_template(source)
        assert result == source

    def test_hidden_block_comment_unchanged(self):
        """Hidden block comments are left unchanged for Django to strip."""
        source = '{% comment "!hide" %}secret{% endcomment %}'
        result = preprocess_template(source)
        assert result == source

    def test_hidden_block_comment_single_quotes(self):
        """Hidden block comments work with single quotes."""
        source = "{% comment '!hide' %}secret{% endcomment %}"
        result = preprocess_template(source)
        assert result == source

    def test_hidden_mixed_with_normal(self):
        """Hidden left unchanged, normal comments converted."""
        source = "{# !hide secret #}{# public #}"
        result = preprocess_template(source)
        assert result == "{# !hide secret #}{% verbatim %}<!-- public -->{% endverbatim %}"

    def test_hidden_inline_preserves_surrounding(self):
        """Content around hidden inline comment is preserved."""
        source = "<p>before</p>{# !hide secret #}<p>after</p>"
        result = preprocess_template(source)
        assert result == source

    def test_hidden_block_preserves_surrounding(self):
        """Content around hidden block comment is preserved."""
        source = '<p>before</p>{% comment "!hide" %}secret{% endcomment %}<p>after</p>'
        result = preprocess_template(source)
        assert result == source

    def test_hidden_multiline_block_unchanged(self):
        """Multi-line hidden block is left unchanged."""
        source = """{% comment "!hide" %}
This is a secret
spanning multiple lines
{% endcomment %}"""
        result = preprocess_template(source)
        assert result == source

    def test_hidden_block_comment_with_note(self):
        """Hidden block comment with note is left unchanged."""
        source = '{% comment "!hide todo" %}secret{% endcomment %}'
        result = preprocess_template(source)
        assert result == source

    def test_hidden_block_comment_with_note_single_quotes(self):
        """Hidden block comment with note works with single quotes."""
        source = "{% comment '!hide todo' %}secret{% endcomment %}"
        result = preprocess_template(source)
        assert result == source

    def test_hidden_inline_with_colon_content(self):
        """Hidden inline with content containing colons is left unchanged."""
        source = "{# !hide key: value #}"
        result = preprocess_template(source)
        assert result == source

    def test_mixed_hidden_and_normal_block(self):
        """Mix of hidden and normal block comments."""
        source = '{% comment "!hide" %}secret{% endcomment %}{% comment %}public{% endcomment %}'
        result = preprocess_template(source)
        assert (
            result == '{% comment "!hide" %}secret{% endcomment %}{% verbatim %}<!-- public -->'
            "{% endverbatim %}"
        )

    def test_hidden_and_normal_interspersed(self):
        """Hidden and normal comments interspersed with content."""
        source = (
            '<div>{# !hide hidden #}{# visible #}{% comment "!hide" %}secret{% endcomment %}'
            "{% comment %}shown{% endcomment %}</div>"
        )
        result = preprocess_template(source)
        assert (
            result == "<div>{# !hide hidden #}{% verbatim %}<!-- visible -->{% endverbatim %}"
            '{% comment "!hide" %}secret{% endcomment %}{% verbatim %}<!-- shown -->'
            "{% endverbatim %}</div>"
        )


class TestRenderMarker:
    """Tests for !render marker (opt-in to process template tags, skip verbatim)."""

    def test_inline_eval_skips_verbatim(self):
        """Inline comment with !render is not wrapped in verbatim."""
        source = "{# !render {{ user.name }} #}"
        result = preprocess_template(source)
        assert result == "<!-- {{ user.name }} -->"

    def test_inline_eval_removes_marker(self):
        """!render marker is removed from output."""
        source = "{# !render some content #}"
        result = preprocess_template(source)
        assert result == "<!-- some content -->"
        assert "!render" not in result

    def test_inline_eval_with_extra_whitespace(self):
        """!render works with extra whitespace."""
        source = "{#   !render   {{ var }}   #}"
        result = preprocess_template(source)
        assert result == "<!-- {{ var }} -->"

    def test_block_eval_skips_verbatim(self):
        """Block comment with !render note is not wrapped in verbatim."""
        source = '{% comment "!render" %}{{ user.name }}{% endcomment %}'
        result = preprocess_template(source)
        assert result == "<!-- {{ user.name }} -->"

    def test_block_eval_single_quotes(self):
        """Block comment with !render works with single quotes."""
        source = "{% comment '!render' %}{{ var }}{% endcomment %}"
        result = preprocess_template(source)
        assert result == "<!-- {{ var }} -->"

    def test_block_eval_with_note(self):
        """Block comment with !render and additional note."""
        source = '{% comment "!render debug" %}{{ user.name }}{% endcomment %}'
        result = preprocess_template(source)
        assert result == "<!-- [debug] {{ user.name }} -->"
        assert "!render" not in result

    def test_block_eval_with_note_single_quotes(self):
        """Block comment with !render and note works with single quotes."""
        source = "{% comment '!render todo' %}{{ var }}{% endcomment %}"
        result = preprocess_template(source)
        assert result == "<!-- [todo] {{ var }} -->"

    def test_inline_eval_escapes_dashes(self):
        """!render comments still escape HTML-unsafe dashes."""
        source = "{# !render foo--bar #}"
        result = preprocess_template(source)
        assert result == "<!-- foo- -bar -->"

    def test_block_eval_escapes_dashes(self):
        """!render block comments still escape HTML-unsafe dashes."""
        source = '{% comment "!render" %}foo--bar{% endcomment %}'
        result = preprocess_template(source)
        assert result == "<!-- foo- -bar -->"

    def test_eval_and_normal_mixed(self):
        """Mix of eval and normal comments."""
        source = "{# !render {{ x }} #}{# {{ y }} #}"
        result = preprocess_template(source)
        assert result == "<!-- {{ x }} -->{% verbatim %}<!-- {{ y }} -->{% endverbatim %}"

    def test_block_eval_multiline(self):
        """Block eval comment with multiline content."""
        source = """{% comment "!render" %}
{{ user.name }}
{{ user.email }}
{% endcomment %}"""
        result = preprocess_template(source)
        assert "<!-- {{ user.name }}" in result
        assert "{{ user.email }}" in result
        assert "{% verbatim %}" not in result


class TestTemplateTagEscaping:
    """Tests verifying template tags are properly escaped by default."""

    def test_inline_variable_escaped(self):
        """Template variable in inline comment is wrapped in verbatim."""
        source = "{# {{ user.secret }} #}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- {{ user.secret }} -->{% endverbatim %}"

    def test_inline_tag_escaped(self):
        """Template tag in inline comment is wrapped in verbatim."""
        source = "{# {% if debug %}show{% endif %} #}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- {% if debug %}show{% endif %} -->{% endverbatim %}"

    def test_block_variable_escaped(self):
        """Template variable in block comment is wrapped in verbatim."""
        source = "{% comment %}{{ user.secret }}{% endcomment %}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- {{ user.secret }} -->{% endverbatim %}"

    def test_block_tag_escaped(self):
        """Template tag in block comment is wrapped in verbatim."""
        source = "{% comment %}{% if debug %}show{% endif %}{% endcomment %}"
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- {% if debug %}show{% endif %} -->{% endverbatim %}"

    def test_block_with_note_escaped(self):
        """Block comment with note still wraps content in verbatim."""
        source = '{% comment "debug" %}{{ value }}{% endcomment %}'
        result = preprocess_template(source)
        assert result == "{% verbatim %}<!-- [debug] {{ value }} -->{% endverbatim %}"


class TestHideRenderPrecedence:
    """Tests verifying !hide always takes precedence over !render."""

    def test_inline_hide_then_eval(self):
        """Inline comment with !hide before !render is hidden."""
        source = "{# !hide !render {{ secret }} #}"
        result = preprocess_template(source)
        assert result == source  # Unchanged, left for Django to strip

    def test_inline_eval_then_hide(self):
        """Inline comment with !render before !hide is still hidden."""
        source = "{# !render !hide {{ secret }} #}"
        result = preprocess_template(source)
        assert result == source  # Unchanged, left for Django to strip

    def test_block_hide_then_eval(self):
        """Block comment with !hide before !render is hidden."""
        source = '{% comment "!hide !render" %}{{ secret }}{% endcomment %}'
        result = preprocess_template(source)
        assert result == source  # Unchanged

    def test_block_eval_then_hide(self):
        """Block comment with !render before !hide is still hidden."""
        source = '{% comment "!render !hide" %}{{ secret }}{% endcomment %}'
        result = preprocess_template(source)
        assert result == source  # Unchanged

    def test_block_eval_then_hide_with_note(self):
        """Block comment with !render !hide and note is still hidden."""
        source = '{% comment "!render !hide debug" %}{{ secret }}{% endcomment %}'
        result = preprocess_template(source)
        assert result == source  # Unchanged

    def test_inline_hide_eval_no_template_processing(self):
        """!hide !render combination should not process template tags."""
        source = "{# !hide !render {{ user.secret }} #}"
        result = preprocess_template(source)
        # Should be unchanged - no processing of {{ user.secret }}
        assert result == source
        assert "user.secret" in result  # Tag still in original form

    def test_inline_eval_hide_no_template_processing(self):
        """!render !hide combination should not process template tags."""
        source = "{# !render !hide {{ user.secret }} #}"
        result = preprocess_template(source)
        # Should be unchanged - no processing of {{ user.secret }}
        assert result == source
        assert "user.secret" in result  # Tag still in original form
