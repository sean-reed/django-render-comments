"""
Template preprocessor for converting Django comments to HTML comments.

Handles two types of Django template comments:
1. Inline comments: {# comment text #}
2. Block comments: {% comment %}...{% endcomment %}

Hidden comments (skipped, not converted - Django strips them normally):
- Inline: {# !hide ... #}
- Block: {% comment "!hide" %}...{% endcomment %}
- Block with note: {% comment "!hide note" %}...{% endcomment %}

Template tag escaping:
- By default, converted comments are wrapped in {% verbatim %} to prevent
  Django from processing any template tags inside the comment content.
- Use !render marker to opt-in to processing template tags:
  - Inline: {# !render {{ var }} #}
  - Block: {% comment "!render" %}{{ var }}{% endcomment %}
  - Block with note: {% comment "!render note" %}{{ var }}{% endcomment %}

Edge cases handled:
- Multi-line block comments
- Comments with optional notes: {% comment "note" %}
- Comments with special characters (-- sequences escaped for HTML safety)
"""

import re

# Pattern for inline comments: {# ... #}
INLINE_COMMENT_PATTERN = re.compile(r"\{#\s*(.*?)\s*#\}", re.DOTALL)

# Pattern for block comments: {% comment %}...{% endcomment %}
# Optional note after comment tag: {% comment "note" %} or {% comment 'note' %}
BLOCK_COMMENT_PATTERN = re.compile(
    r"\{%\s*comment(?:\s+[\"']([^\"']*)[\"'])?\s*%\}"  # Opening tag with optional note
    r"(.*?)"  # Comment content (non-greedy)
    r"\{%\s*endcomment\s*%\}",  # Closing tag
    re.DOTALL,
)


def escape_html_comment(text: str) -> str:
    """
    Escape text for safe inclusion in HTML comments.

    HTML comments cannot contain '--' sequences as they would prematurely
    close the comment. This function replaces them with a safe alternative.

    Args:
        text: The raw comment text.

    Returns:
        Escaped text safe for HTML comments.
    """
    # Replace -- with a safe alternative to prevent breaking HTML comments
    return text.replace("--", "- -")


def _convert_inline_comment(match: re.Match[str]) -> str:
    """
    Convert a Django inline comment to an HTML comment.

    Hidden comments ({# !hide ... #}) are skipped and left unchanged
    for Django to strip during normal template rendering.

    By default, output is wrapped in {% verbatim %} to prevent Django from
    processing any template tags in the comment content. Use !render marker
    to opt-in to processing: {# !render {{ var }} #}

    Note: !hide always takes precedence over !render. If both markers are
    present (in any order), the comment is hidden.

    Args:
        match: Regex match object containing the comment content.

    Returns:
        HTML comment string (wrapped in verbatim), or original if hidden.
    """
    content = match.group(1)
    stripped = content.lstrip()

    # Skip hidden comments - leave for Django to strip
    # !hide takes precedence over !render, so check for !hide anywhere in markers
    if stripped.startswith("!hide"):
        return match.group(0)
    if stripped.startswith("!render") and stripped[7:].lstrip().startswith("!hide"):
        return match.group(0)

    # Check for !render marker - process tags, don't wrap in verbatim
    if stripped.startswith("!render"):
        content = stripped[7:].lstrip()  # Remove !render prefix
        escaped = escape_html_comment(content)
        return f"<!-- {escaped} -->"

    # Default: wrap in verbatim to escape template tags
    escaped = escape_html_comment(content)
    return f"{{% verbatim %}}<!-- {escaped} -->{{% endverbatim %}}"


def _convert_block_comment(match: re.Match[str]) -> str:
    """
    Convert a Django block comment to an HTML comment.

    Hidden comments ({% comment "!hide" %} or {% comment "!hide note" %})
    are skipped and left unchanged for Django to strip during normal template
    rendering.

    By default, output is wrapped in {% verbatim %} to prevent Django from
    processing any template tags in the comment content. Use !render marker
    to opt-in to processing: {% comment "!render" %} or {% comment "!render note" %}

    Note: !hide always takes precedence over !render. If both markers are
    present (in any order), the comment is hidden.

    Args:
        match: Regex match object containing optional note and content.

    Returns:
        HTML comment string (wrapped in verbatim), with note prefix if present,
        or original if hidden.
    """
    note = match.group(1)  # Optional note from {% comment "note" %}
    content = match.group(2)

    # Skip hidden comments - leave for Django to strip
    # !hide takes precedence over !render, so check for !hide anywhere in note
    if note and note.startswith("!hide"):
        return match.group(0)
    if note and note.startswith("!render") and "!hide" in note:
        return match.group(0)

    # Check for !render marker - process tags, don't wrap in verbatim
    eval_mode = False
    display_note = note
    if note and note.startswith("!render"):
        eval_mode = True
        # Remove !render prefix from note, keep remaining note text if any
        display_note = note[7:].lstrip() or None

    escaped_content = escape_html_comment(content.strip())

    if display_note:
        escaped_note = escape_html_comment(display_note)
        html_comment = f"<!-- [{escaped_note}] {escaped_content} -->"
    else:
        html_comment = f"<!-- {escaped_content} -->"

    if eval_mode:
        return html_comment

    # Default: wrap in verbatim to escape template tags
    return f"{{% verbatim %}}{html_comment}{{% endverbatim %}}"


def preprocess_template(source: str) -> str:
    """
    Convert all Django comments in template source to HTML comments.

    Hidden comments (!hide inline or "!hide" block) are skipped and
    left unchanged for Django to strip during normal template rendering.

    Args:
        source: The raw template source code.

    Returns:
        Template source with Django comments converted to HTML comments.
    """
    # Process block comments first (they may contain inline comment syntax)
    result = BLOCK_COMMENT_PATTERN.sub(_convert_block_comment, source)

    # Then process inline comments
    result = INLINE_COMMENT_PATTERN.sub(_convert_inline_comment, result)

    return result
