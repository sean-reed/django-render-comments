# django-render-comments

[![CI](https://github.com/sean-reed/django-render-comments/actions/workflows/ci.yml/badge.svg)](https://github.com/sean-reed/django-render-comments/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/django-render-comments)](https://pypi.org/project/django-render-comments/)
[![Python](https://img.shields.io/pypi/pyversions/django-render-comments)](https://pypi.org/project/django-render-comments/)
[![License](https://img.shields.io/pypi/l/django-render-comments)](https://github.com/sean-reed/django-render-comments/blob/main/LICENSE.txt)

Render Django template comments as HTML comments in DEBUG mode.

## Overview

This Django app converts Django template comments into HTML comments when `DEBUG=True`,
making them visible in the page source and browser developer tools.

Normally, [Django template comments](https://docs.djangoproject.com/en/stable/ref/templates/language/#comments) (`{# comment #}` and
[`{% comment %}...{% endcomment %}`](https://docs.djangoproject.com/en/stable/ref/templates/builtins/#comment)) are stripped out during template processing, so they do not
appear in the rendered HTML output. With this app installed, these comments
are transformed into HTML comments (`<!-- comment -->`) instead when `DEBUG=True`, allowing developers to see them
directly in the rendered HTML. This is useful for debugging, documentation, and 
collaboration. When `DEBUG=False`, comments are stripped and everything inside them is ignored (not parsed) as usual by Django's template engine.

An alternative would be to use HTML comments 
directly in templates, as these are not stripped by Django, but that approach has some downsides:

- They are included in the rendered output in production (i.e. when `DEBUG=False`), increasing the HTML payload size and potentially 
exposing internal notes, debugging information, or other sensitive information to end users.
- HTML comments are not ignored by the Django template engine so 
any content inside them (e.g. `<!-- {% if user.is_authenticated %}...{% endif %} -->`) will still be processed by
the Django template engine, potentially causing errors or unintended behavior (e.g. [see this Stack Overflow post](https://stackoverflow.com/questions/37050172/why-django-finds-errors-inside-comment-blocks-in-template/79365925#79365925)).

By using this app, developers can use Django's comment tags for all their comments, and have them
visible during development and automatically stripped out in production.

### Additional Features

Any comments that should always
be hidden (even when `DEBUG=True`) can be marked with a special `!hide` marker to ensure they are never rendered
in the output HTML. 

By default, the content from comments will be shown verbatim in the rendered HTML comment and any tags or filters it includes will be ignored by Django's template engine during processing, 
matching Django's standard behavior. However, adding a `!render` marker to the comment overrides this so that template tags and filters in the content are processed.

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

By default, any template tags it contains appear literally in the HTML output and are not processed by Django's template engine. This matches how Django's comments normally 
behave during template rendering.

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

For debugging scenarios where you want tags and filters in a comment's content to be processed, for example to see actual variable values, 
simply add a `!render` marker to the comment as shown below:

| Comment Type | Syntax |
|--------------|--------|
| Inline | `{# !render user={{ user.name }} #}` |
| Block | `{% comment "!render" %}{{ value }}{% endcomment %}` |
| Block with note | `{% comment "!render note" %}{{ value }}{% endcomment %}` |
| Block with dynamic note | `{% comment "!render {{ var }}" %}{{ value }}{% endcomment %}` |

### Example
```html
{# !render Current user: {{ user.username }} #}
{% comment "!render {{ request.method }}" %}
Request ID: {{ request.id }}
{% endcomment %}
```

With `DEBUG=True` and `user.username="john"`, `request.method="GET"`, `request.id="abc123"`, renders as:
```html
<!-- Current user: john -->
<!-- [GET] Request ID: abc123 -->
```

The `!render` marker is removed from the output, and template tags are processed (both in the note and in the comment body). Important: Template rendering will only occur when `DEBUG=True`, so you will usually want to ensure the content does not have side effects outside of the comment (e.g. modifying context variables) that is relied on elsewhere as it will be ignored when `DEBUG=False`.

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
