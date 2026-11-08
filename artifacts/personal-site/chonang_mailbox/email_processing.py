"""Processing and storage of incoming email messages."""

import logging
import re
import uuid
from email.utils import parseaddr
from io import BytesIO
from pathlib import PurePosixPath

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import EmailAttachment, EmailMessage, EmailThread
from .resend_client import (
    ResendAPIError,
    download_received_attachment,
    get_received_email,
    list_received_attachments,
)
from .storage import delete_attachment, upload_attachment

logger = logging.getLogger(__name__)


def _extract_email_address(value):
    """Extract an email address from a From header."""
    if isinstance(value, str):
        return parseaddr(value)[1] or value
    return ""


def _get_header_value(headers, name):
    """Find a header without depending on its capitalization."""
    if not isinstance(headers, dict):
        return ""

    for key, value in headers.items():
        if key.lower() == name.lower():
            return value if isinstance(value, str) else ""

    return ""


def _split_message_ids(value):
    """Split References into individual message IDs."""
    if not isinstance(value, str):
        return []

    return re.findall(r"<[^>]+>", value)


def _find_thread(message_id, in_reply_to, references):
    """Find an existing conversation using email reply headers."""
    related_ids = []

    if in_reply_to:
        related_ids.append(in_reply_to)

    related_ids.extend(_split_message_ids(references))

    for related_id in related_ids:
        existing = EmailMessage.objects.filter(
            message_id=related_id
        ).first()

        if existing:
            return existing.thread

    return None


def process_received_email(resend_email_id):
    """Retrieve and save an incoming email, avoiding duplicates."""

    uploaded_keys = []

    try:
        with transaction.atomic():
            existing = EmailMessage.objects.filter(
                resend_email_id=resend_email_id
            ).first()

            if existing:
                return existing, False

            email_data = get_received_email(resend_email_id)

            headers = email_data.get("headers") or {}
            message_id = (
                email_data.get("message_id")
                or _get_header_value(headers, "Message-ID")
            )
            in_reply_to = _get_header_value(headers, "In-Reply-To")
            references = _get_header_value(headers, "References")

            thread = _find_thread(
                message_id,
                in_reply_to,
                references,
            )

            if not thread:
                thread = EmailThread.objects.create(
                    subject=email_data.get("subject") or ""
                )

            created_at = parse_datetime(
                email_data.get("created_at", "")
            )

            if created_at and timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)

            sender = _extract_email_address(
                email_data.get("from", "")
            )

            message = EmailMessage.objects.create(
                thread=thread,
                resend_email_id=resend_email_id,
                message_id=message_id or "",
                in_reply_to=in_reply_to,
                references=_split_message_ids(references),
                direction=EmailMessage.INCOMING,
                sender=sender,
                recipients=email_data.get("to") or [],
                cc=email_data.get("cc") or [],
                bcc=email_data.get("bcc") or [],
                subject=email_data.get("subject") or "",
                body_text=email_data.get("text") or "",
                body_html=email_data.get("html") or "",
                headers=headers,
                is_read=False,
                received_at=created_at,
            )

            thread.last_message_at = created_at or timezone.now()
            thread.save(
                update_fields=["last_message_at", "updated_at"]
            )

            store_email_attachments(
                message,
                resend_email_id,
                uploaded_keys,
            )

        return message, True

    except Exception:
        # The database transaction has rolled back at this point.
        # Remove any files uploaded during the failed transaction.
        for object_key in uploaded_keys:
            try:
                delete_attachment(object_key)
            except Exception:
                logger.exception(
                    "Could not clean up R2 object %s",
                    object_key,
                )

        raise

def store_email_attachments(
    message,
    resend_email_id,
    uploaded_keys,
):
    """Download incoming attachments and store them privately in R2."""

    attachments = list_received_attachments(resend_email_id)

    for attachment in attachments:
        download_url = attachment.get("download_url")

        if not download_url:
            raise ResendAPIError(
                "Attachment has no download URL."
            )

        content = download_received_attachment(download_url)

        original_filename = attachment.get("filename") or "attachment"
        filename = PurePosixPath(
            original_filename.replace("\\", "/")
        ).name

        filename = "".join(
            char for char in filename
            if char.isprintable() and char not in "/\\"
        )[:255] or "attachment"

        content_type = (
            attachment.get("content_type")
            or "application/octet-stream"
        )

        object_key = f"mail/{message.pk}/{uuid.uuid4().hex}"

        upload_attachment(
            BytesIO(content),
            object_key,
            content_type,
        )

        # Track the upload immediately so it can be cleaned up
        # if the database transaction subsequently fails.
        uploaded_keys.append(object_key)

        EmailAttachment.objects.create(
            message=message,
            filename=filename,
            content_type=content_type,
            size_bytes=len(content),
            storage_key=object_key,
            content_id=attachment.get("content_id") or "",
            is_inline=(
                attachment.get("content_disposition") == "inline"
            ),
        )
