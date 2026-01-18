# django-render-comments

[![CI](https://github.com/sean-reed/django-render-comments/actions/workflows/ci.yml/badge.svg)](https://github.com/sean-reed/django-render-comments/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/django-render-comments)](https://pypi.org/project/django-render-comments/)
[![Python](https://img.shields.io/pypi/pyversions/django-render-comments)](https://pypi.org/project/django-render-comments/)
[![License](https://img.shields.io/pypi/l/django-render-comments)](https://github.com/sean-reed/django-render-comments/blob/main/LICENSE)

Render Django template comments as HTML comments in DEBUG mode.

## Overview

This Django app converts Django template comments into HTML comments when `DEBUG=True`,
making them visible in the page source and browser developer tools.

Normally, Django template comments (e.g. `{# comment #}` and
`{% comment %}...{% endcomment %}`) are stripped out during template processing, so they do not
appear in the final HTML output. With this app installed and `DEBUG=True`, these comments
are transformed into HTML comments (`<!-- comment -->`) instead, allowing developers to see them
directly in the rendered HTML. This is useful for debugging, documentation, and 
collaboration. The alternative is to use HTML comments 
directly in templates, as these are not stripped by Django, but they have some drawbacks:

- They are included in the rendered output in production (i.e. when `DEBUG=False`), increasing the HTML payload size and potentially 
exposing internal notes, debugging information, or other sensitive information to end users.
- HTML comments are not ignored by the Django template engine so 
any content inside them (e.g. `<!-- {% if user.is_authenticated %}...{% endif %} -->`) will still be processed by
the Django template engine, potentially causing errors or unintended behavior (e.g. [see this Stack Overflow post](https://stackoverflow.com/questions/37050172/why-django-finds-errors-inside-comment-blocks-in-template/79365925#79365925)).

By using this app, developers can use Django's comment tags for all their comments, and have them
visible during development and automatically stripped out in production. 

Any comments that should always
be hidden (even when `DEBUG=True`) can be marked with a special `!hide` marker to ensure they are never rendered
in the output HTML. Comment content appears verbatim and any tags it includes are not parsed by Django's template engine, matching Django's standard behavior, but 
content can optionally be rendered too by adding a `!render` marker to the comment.

When `DEBUG=False`, comments are stripped and everything inside them is ignored (not parsed) as usual by Django's template engine.

To disable the app from processing comments when `DEBUG=True` you can set the `RENDER_COMMENTS_ENABLED` setting to `False`.

## Installation

```bash
pip install django-render-comments
```

Or with uv:

```bash
uv add django-render-comments
```

## Quick Start

In your Django `settings.py`:

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
RENDER_COMMENTS_ENABLED = False  # App will not process comments, even if DEBUG=True.
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

## Comment Content Rendering

By default, each comment is wrapped in Django's [`{% verbatim %}`](https://docs.djangoproject.com/en/stable/ref/templates/builtins/#verbatim) tags after 
conversion to HTML so any template tags it contains appear literally in the HTML output and are not processed by Django's template engine. This matches how Django's 
comments normally behave (i.e. they are ignored by the template engine).

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

### Opt-in Processing with `!render`

For debugging scenarios where you want to see actual variable values in comments, use the `!render` marker. This skips the `{% verbatim %}` wrapping and allows Django to process template tags within the comment:

| Comment Type | Syntax |
|--------------|--------|
| Inline | `{# !render user={{ user.name }} #}` |
| Block | `{% comment "!render" %}{{ value }}{% endcomment %}` |
| Block with note | `{% comment "!render debug" %}{{ value }}{% endcomment %}` |

### Example
```html
{# !render Current user: {{ user.username }} #}
{% comment "!render debug" %}
Request ID: {{ request.id }}
{% endcomment %}
```

With `DEBUG=True` and `user.username="john"`, `request.id="abc123"`, renders as:
```html
<!-- Current user: john -->
<!-- [debug] Request ID: abc123 -->
```

The `!render` marker is removed from the output, and template tags are processed (not wrapped in `{% verbatim %}`). Important: Template rendering will only occur when `DEBUG=True`, so you will usually want to ensure the content does not have side effects outside of the comment (e.g. modifying context variables) that is relied on elsewhere as it will be ignored when `DEBUG=False`.

### Marker Precedence

If both `!hide` and `!render` markers are present in a comment (in any order), `!hide` always takes precedence. The comment will be hidden and no template processing will occur.

```html
{# !hide !render {{ secret }} #}        {# Hidden - !hide wins #}
{# !render !hide {{ secret }} #}        {# Also hidden - !hide still wins #}
{% comment "!render !hide" %}...{% endcomment %}  {# Hidden #}
```

This ensures that marking a comment as hidden cannot be accidentally bypassed by also adding `!render`.

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

- Python 3.10+
- Django 4.2, 5.0, 5.1, 5.2, or 6.0

## Development

```bash
# Clone the repository
git clone https://github.com/sean-reed/django-render-comments
cd django-render-comments

# Install dependencies
uv sync --group dev

# Run tests (current environment)
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Run full test matrix (Python 3.10-3.13 x Django 4.2-6.0)
uv run nox

# Run specific Python/Django combination
uv run nox -s "tests-3.10(django='4.2')"

# Run linting
uv run nox -s lint

# Run type checking
uv run nox -s typecheck

# List all available test sessions
uv run nox --list
```

## License

MIT License
