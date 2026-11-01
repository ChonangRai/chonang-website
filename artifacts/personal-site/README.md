# Personal Website

A small Django project for a personal website. The page is rendered on the server with Django templates; its styling uses plain CSS. SQLite is Django's default local database, so no database service is needed for this first version.

## Run locally

From this folder:

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open the local address shown by Django, usually `http://127.0.0.1:8000/`. The `migrate` command creates `db.sqlite3` and Django's built-in tables.

## Important files

- `manage.py` — starts Django management commands, including the development server and database migrations.
- `config/settings.py` — project settings: installed apps, middleware, templates, SQLite, and static files.
- `config/urls.py` — connects top-level website URLs to the `core` app.
- `config/wsgi.py` and `config/asgi.py` — standard entry points for web servers; they are included for future deployment options.
- `core/apps.py` — tells Django about the `core` app.
- `core/urls.py` — maps the homepage URL to its view.
- `core/views.py` — selects and renders the homepage template.
- `templates/base.html` — shared HTML document, navigation, accessibility link, and footer.
- `templates/core/home.html` — the introductory homepage content.
- `static/css/site.css` — responsive layout, typography, colours, and mobile styles.
- `requirements.txt` — the Python package needed by this project: Django.
- `db.sqlite3` — created locally by `migrate`; it is intentionally not committed.

Replace “Your Name” and the sample introduction in `templates/base.html` and `templates/core/home.html` with your own details.

The included development settings are for learning and local preview. Before publishing, set a private `DJANGO_SECRET_KEY`, turn `DJANGO_DEBUG` off, and set `DJANGO_ALLOWED_HOSTS` to the website's host name.
