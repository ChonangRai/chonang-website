---
name: Django manifest static assets
description: The personal site's collected static files use compressed manifest storage.
---

**Rule:** After changing files under `static/`, run `python manage.py collectstatic --noinput` from the Django project directory and restart the Django workflow before checking the rendered page.

**Why:** WhiteNoise's compressed manifest storage serves versioned asset URLs from `staticfiles/`. The preview continued to serve an older hashed CSS file until the generated manifest and assets were refreshed and the server restarted.

**How to apply:** Use this for stylesheet or static-image changes. The collected output is generated; do not change Django deployment settings just to refresh it.
