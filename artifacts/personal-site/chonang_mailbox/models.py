
"""Database models for the private Chonang Mail mailbox."""

from django.db import models


class EmailThread(models.Model):
    """A conversation containing related email messages."""

    subject = models.CharField(max_length=998, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_message_at", "-created_at"]

    def __str__(self):
        return self.subject or "No subject"


class EmailMessage(models.Model):
    """An individual incoming or outgoing email."""

    INCOMING = "incoming"
    OUTGOING = "outgoing"

    DIRECTION_CHOICES = [
        (INCOMING, "Incoming"),
        (OUTGOING, "Outgoing"),
    ]

    thread = models.ForeignKey(
        EmailThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    resend_email_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    message_id = models.CharField(max_length=998, blank=True)
    in_reply_to = models.CharField(max_length=998, blank=True)
    references = models.JSONField(default=list, blank=True)

    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
    )

    sender = models.EmailField(max_length=320)
    recipients = models.JSONField(default=list, blank=True)
    cc = models.JSONField(default=list, blank=True)
    bcc = models.JSONField(default=list, blank=True)

    subject = models.CharField(max_length=998, blank=True)
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    headers = models.JSONField(default=dict, blank=True)

    is_read = models.BooleanField(default=False)
    received_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.subject or f"Email from {self.sender}"


class EmailAttachment(models.Model):
    """Metadata for an attachment stored privately in Cloudflare R2."""

    message = models.ForeignKey(
        EmailMessage,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)

    storage_key = models.CharField(max_length=1024, unique=True)

    content_id = models.CharField(max_length=255, blank=True)
    is_inline = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename
