# django-render-comments

Render Django template comments as HTML comments in DEBUG mode.

## Overview

This Django app converts Django template comments into HTML comments when `DEBUG=True`,
making them visible in the page source and browser developer tools.

Normally, Django template comments (e.g. `{# comment #}` and
`{% comment %}...{% endcomment %}`) are stripped out during template rendering, so they do not
appear in the final HTML output. With this app installed and `DEBUG=True`, these comments
are transformed into HTML comments (`<!-- comment -->`), allowing developers to see them
directly in the rendered HTML. This is useful for debugging, documentation, and 
collaboration. The alternative is to use HTML comments 
directly in templates, as these are not stripped by Django, but they have some drawbacks:


1. They are included in the rendered output in production (i.e. when `DEBUG=False`), increasing the HTML payload size and potentially 
exposing internal notes, debugging information, or other sensitive information to end users.
2. HTML comments are not ignored by the Django template engine so 
any content inside them (e.g. `<!-- {% if user.is_authenticated %}...{% endif %} -->`) will still be processed by
the Django template engine, potentially causing errors or unintended behavior (e.g. [this Stack Overflow post](https://stackoverflow.com/questions/37050172/why-django-finds-errors-inside-comment-blocks-in-template/79365925#79365925)).

By using this app, developers can keep all their comments in Django template syntax, and have them
visible during development and automatically stripped out in production. Any comments that should always
be hidden (even when `DEBUG=True`) can be marked with a special `!hide` marker to ensure they are never rendered
in the output HTML. Anything inside comments is escaped by default to prevent parsing by Django's template engine and
exposure of sensitive data or template errors, matching Django's standard behavior, but can optionally be evaluated 
when `DEBUG=True` by adding an `!eval` marker to the comment.

When `DEBUG=False`, comments are stripped and everything inside them is ignored (not parsed) as usual.

To disable the feature even in `DEBUG` mode, you can set the `RENDER_COMMENTS_ENABLED` setting to `False`.

## Installation

```bash
pip install django-render-comments
```

Or with uv:

```bash
uv add django-render-comments
```

## Quick Start

1. **Add to INSTALLED_APPS** (optional, for app registry):

```python
INSTALLED_APPS = [
    # ...
    'django_render_comments',
]
```

2. **Configure template loaders**:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'OPTIONS': {
            'loaders': [
                'django_render_comments.loaders.filesystem.Loader',
                'django_render_comments.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                # ... other context processors
            ],
        },
    },
]
```

**Note**: When specifying custom loaders, `APP_DIRS` must not be set (or be `False`).

## How It Works

### Before (Django default)

Template:
```html
<div>
    {# Debug: user={{ user }} #}
    {% comment %}Old navigation{% endcomment %}
    <nav>...</nav>
</div>
```

Output (comments stripped):
```html
<div>


    <nav>...</nav>
</div>
```

### After (with django-render-comments, DEBUG=True)

Output (comments visible in HTML, template tags appear literally):
```html
<div>
    <!-- Debug: user={{ user }} -->
    <!-- Old navigation -->
    <nav>...</nav>
</div>
```

Note: Template tags like `{{ user }}` appear literally in the comment output - they are **not** processed by Django's template engine. This matches the behavior of Django's native `{% comment %}` block, which protects its content from being processed.

## Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `DEBUG` | bool | False | Comments only converted when True |
| `RENDER_COMMENTS_ENABLED` | bool | True | Set to False to disable even in DEBUG mode |

### Disabling the Feature

```python
# settings.py
DEBUG = True
RENDER_COMMENTS_ENABLED = False  # Comments will be stripped, not converted
```

## Comment Syntax Support

| Django Syntax | Converted To |
|---------------|--------------|
| `{# comment #}` | `<!-- comment -->` |
| `{% comment %}...{% endcomment %}` | `<!-- ... -->` |
| `{% comment "note" %}...{% endcomment %}` | `<!-- [note] ... -->` |

## Hidden Comments

Sometimes you may want to keep a comment out of HTML output, even during development. Use the
`!hide` marker for inline comments or `"!hide"` note for block comments to ensure they are
always stripped.

### Syntax

| Comment Type | Normal (converted to HTML) | Hidden (always stripped) |
|--------------|---------------------------|--------------------------|
| Inline | `{# comment #}` | `{# !hide comment #}` |
| Block | `{% comment %}...{% endcomment %}` | `{% comment "!hide" %}...{% endcomment %}` |
| Block with note | `{% comment "note" %}...{% endcomment %}` | `{% comment "!hide note" %}...{% endcomment %}` |

### Behavior

| Condition | Normal comments | Hidden comments |
|-----------|-----------------|-----------------|
| App installed, DEBUG=True | Converted to HTML comment | Stripped |
| App installed, DEBUG=False | Stripped | Stripped |
| App NOT installed | Stripped | Stripped |

### Example
```html
<div>
    {# !hide TODO: Fix security issue in auth flow #}
    {% comment "!hide" %}
    Internal: This endpoint bypasses rate limiting
    {% endcomment %}
    {% comment "!hide todo - fix auth" %}
    Temporary workaround for authentication
    {% endcomment %}
    <p>Content</p>
</div>
```

With `DEBUG=True`, renders as:
```html
<div>
    <p>Content</p>
</div>
```

The hidden comments are completely removed from the output.

## Template Tag Escaping

By default, template tags inside comments are **escaped** - they appear literally in the HTML output and are not processed by Django's template engine. This prevents:

1. **Accidental data exposure**: Commented-out code like `{# {{ user.email }} #}` won't leak the actual email
2. **Template errors**: Commented-out code like `{% if %}` blocks won't cause syntax errors
3. **Unexpected behavior**: Commented code behaves as truly "commented out"

This matches how Django's native `{% comment %}` block works - content inside is protected from processing.

### Example
```html
{# Debug: user={{ user.email }} #}
{% comment %}{% if debug %}show{% endif %}{% endcomment %}
```

With `DEBUG=True`, renders as:
```html
<!-- Debug: user={{ user.email }} -->
<!-- {% if debug %}show{% endif %} -->
```

The template tags appear literally - `{{ user.email }}` is NOT replaced with the actual email.

### Opt-in Processing with `!eval`

For debugging scenarios where you want to see actual variable values in comments, use the `!eval` marker:

| Comment Type | Syntax |
|--------------|--------|
| Inline | `{# !eval user={{ user.name }} #}` |
| Block | `{% comment "!eval" %}{{ value }}{% endcomment %}` |
| Block with note | `{% comment "!eval debug" %}{{ value }}{% endcomment %}` |

### Example
```html
{# !eval Current user: {{ user.username }} #}
{% comment "!eval debug" %}
Request ID: {{ request.id }}
{% endcomment %}
```

With `DEBUG=True` and `user.username="john"`, `request.id="abc123"`, renders as:
```html
<!-- Current user: john -->
<!-- [debug] Request ID: abc123 -->
```

The `!eval` marker is removed from the output, and template tags are processed. Important: Evaluation will only occur when `DEBUG=True` so you will usually want
to ensure the content does not have side effects outside of the comment (e.g. modifying context variables used elsewhere) as it will be ignored when `DEBUG=False`.

### Marker Precedence

If both `!hide` and `!eval` markers are present in a comment (in any order), `!hide` always takes precedence. The comment will be hidden and no template processing will occur.

```html
{# !hide !eval {{ secret }} #}        {# Hidden - !hide wins #}
{# !eval !hide {{ secret }} #}        {# Also hidden - !hide still wins #}
{% comment "!eval !hide" %}...{% endcomment %}  {# Hidden #}
```

This ensures that marking a comment as hidden cannot be accidentally bypassed by also adding `!eval`.

## Edge Cases & Limitations

1. **Comments in JavaScript strings**: Comment patterns inside `<script>` tags will
   also be converted. If you have JavaScript containing `{# ... #}` as string literals,
   they will be transformed.

2. **Comment patterns in attributes**: `<div data-info="{# test #}">` will become
   `<div data-info="<!-- test -->">`.

3. **Nested HTML comments**: If your Django comments contain `--`, they will be
   escaped to `- -` to prevent breaking HTML comment syntax.

4. **Performance**: The preprocessing adds minimal overhead as it uses compiled
   regex patterns and only runs in DEBUG mode.

## Requirements

- Python 3.12+
- Django 4.2+

## Development

```bash
# Clone the repository
git clone https://github.com/sean-reed/django-render-comments
cd django-render-comments

# Install with uv
uv sync --group dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Type checking
uv run pyright

# Linting
uv run ruff check src tests
```

## License

MIT License
