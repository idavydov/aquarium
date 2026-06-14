# Repository Guidelines

## Project Structure & Module Organization

This repository contains a static chord archive for Аквариум/BG. Source pages live in `content/аккорды/` as Jinja-backed HTML files. Shared layouts are in `templates/`; generated output goes to `public/`. Static assets such as Bootstrap CSS, JavaScript, fonts, favicon, and images live in `static/`. Utility and migration scripts are in `bin/`. The `old/` directory is historical source material; avoid editing it unless doing data recovery or migration.

## Build, Test, and Development Commands

- `bin/gen_static.py`: renders `content/` through `templates/` into `public/`.
- `rsync -av --delete --recursive --exclude '*~' static/ public`: refreshes static assets in `public/`.
- `bin/install.sh user@host:/remote/path/`: full publish script; it syncs static files, renders pages, then deploys `public/` over SSH. Use `DEPLOY_RSYNC_PATH='sudo rsync'` when the remote path needs sudo.
- `bin/checkurls.sh log`: checks logged `aquarium.myths.ru` URLs with `curl` and reports non-200 responses.

There is no package manifest or dedicated dev server. For local inspection, build `public/` and serve it from that directory, for example `python -m SimpleHTTPServer 8000`.

## Coding Style & Naming Conventions

Keep existing formatting and encoding conventions. Python scripts are short, procedural UTF-8 files; preserve the local indentation style when editing. Shell scripts use Bash and should quote paths and variables that may contain Cyrillic names or spaces.

Chord files should follow the established pattern:

```jinja
{% extends "chords.html" %}
{% set title = "Song Title" %}
{% block content %}
{% raw %}
...
{% endraw %}
{% endblock %}
```

Use descriptive filenames under `content/аккорды/`, matching the existing underscore-separated song names.

## Testing Guidelines

No automated test suite is currently present. Treat a successful static render as the baseline check. After content changes, verify the generated page under `public/аккорды/` and confirm the index includes the expected title. After link changes, run `bin/checkurls.sh` against the relevant log file.

## Commit & Pull Request Guidelines

Recent commits use short summaries such as `escape urls`, `check urls script`, and `remove robots txt`. Keep commit subjects concise and focused. Pull requests should describe affected content or script behavior, list commands run, and include screenshots only for visual output or formatting changes.

## Agent-Specific Instructions

Do not edit generated `public/` files by hand unless explicitly requested; change `content/`, `templates/`, or `static/` and regenerate instead. Preserve Cyrillic filenames and text exactly, and avoid broad cleanup in historical `old/` data.
