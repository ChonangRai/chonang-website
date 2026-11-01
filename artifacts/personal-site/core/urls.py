"""URL routes for the core app."""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("academic-work/", views.academic_work, name="academic_work"),
    path("projects/", views.projects, name="projects"),
    path("writing/", views.writing, name="writing"),
    path("poetry-cinema/", views.poetry_cinema, name="poetry_cinema"),
    path("contact/", views.contact, name="contact"),
    path("privacy/", views.privacy, name="privacy"),
]
