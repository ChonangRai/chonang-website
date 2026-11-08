
"""Admin configuration for Chonang Mail."""

from django.contrib import admin

from .models import EmailAttachment, EmailMessage, EmailThread


class EmailAttachmentInline(admin.TabularInline):
    model = EmailAttachment
    extra = 0
    readonly_fields = (
        "filename",
        "content_type",
        "size_bytes",
        "storage_key",
        "created_at",
    )


class EmailMessageInline(admin.TabularInline):
    model = EmailMessage
    extra = 0
    readonly_fields = (
        "sender",
        "direction",
        "subject",
        "received_at",
        "sent_at",
    )


@admin.register(EmailThread)
class EmailThreadAdmin(admin.ModelAdmin):
    list_display = ("subject", "created_at", "last_message_at")
    search_fields = ("subject",)
    inlines = (EmailMessageInline,)


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "sender",
        "direction",
        "is_read",
        "received_at",
    )
    list_filter = ("direction", "is_read")
    search_fields = ("subject", "sender", "resend_email_id")
    readonly_fields = ("created_at", "resend_email_id")
    inlines = (EmailAttachmentInline,)


@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    list_display = ("filename", "content_type", "size_bytes", "created_at")
    search_fields = ("filename", "storage_key")
    readonly_fields = ("storage_key", "created_at")
