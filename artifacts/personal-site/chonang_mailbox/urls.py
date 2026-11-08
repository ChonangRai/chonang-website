"""URL configuration for Chonang Mail."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.resend_webhook, name="resend_webhook"),
]
