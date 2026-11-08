"""Top-level URL configuration."""

from django.contrib import admin
from django.urls import include, path
from chonang_mailbox import views as mailbox_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "mail/attachments/<int:attachment_id>/download/",
        mailbox_views.download_attachment,
        name="download_attachment",
    ),
    path("", include("core.urls")),
    path("webhooks/resend/", include("chonang_mailbox.urls")),
]