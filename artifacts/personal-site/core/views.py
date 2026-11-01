"""Views for the core app."""

from django.shortcuts import render


def home(request):
    """Render the single-page personal site."""
    return render(request, "core/home.html")
