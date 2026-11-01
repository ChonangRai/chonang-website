"""Page views for the personal website."""

from django.shortcuts import render


def _render_page(request, template_name, active_page):
    """Render a page with the navigation item that should be marked current."""
    return render(
        request,
        template_name,
        {"active_page": active_page},
    )


def home(request):
    """Render the homepage introduction."""
    return _render_page(request, "core/home.html", "home")


def about(request):
    """Render the personal background page."""
    return _render_page(request, "core/about.html", "about")


def academic_work(request):
    """Render the academic research page."""
    return _render_page(request, "core/academic_work.html", "academic_work")


def projects(request):
    """Render the practical projects page."""
    return _render_page(request, "core/projects.html", "projects")


def writing(request):
    """Render the writing landing page."""
    return _render_page(request, "core/writing.html", "writing")


def poetry_cinema(request):
    """Render the poetry and cinema landing page."""
    return _render_page(request, "core/poetry_cinema.html", "poetry_cinema")


def contact(request):
    """Render the contact information page."""
    return _render_page(request, "core/contact.html", "contact")


def privacy(request):
    """Render the privacy and cookies policy."""
    return _render_page(request, "core/privacy.html", "privacy")
