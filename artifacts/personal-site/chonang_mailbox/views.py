"""Views for Chonang Mail."""

import json
import logging

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import IntegrityError
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from svix.webhooks import Webhook, WebhookVerificationError

from .email_processing import process_received_email
from .models import EmailAttachment, EmailMessage
from .storage import create_download_url
from .resend_client import ResendAPIError


logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def resend_webhook(request):
    """Verify and process incoming Resend webhook events."""

    secret = settings.RESEND_WEBHOOK_SECRET

    if not secret:
        return JsonResponse(
            {"error": "Webhook is not configured."},
            status=503,
        )

    try:
        webhook = Webhook(secret)
        webhook.verify(request.body, request.headers)
    except WebhookVerificationError:
        logger.warning("Rejected Resend webhook with invalid signature.")
        return JsonResponse(
            {"error": "Invalid webhook signature."},
            status=400,
        )
    except Exception:
        logger.exception("Resend webhook verification failed.")
        return JsonResponse(
            {"error": "Webhook verification failed."},
            status=400,
        )

    try:
        event = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "Invalid JSON payload."},
            status=400,
        )

    if not isinstance(event, dict):
        return JsonResponse(
            {"error": "Invalid event format."},
            status=400,
        )

    if event.get("type") != "email.received":
        return JsonResponse({"ignored": True}, status=200)

    data = event.get("data")

    if not isinstance(data, dict):
        return JsonResponse(
            {"error": "Missing event data."},
            status=400,
        )

    email_id = data.get("email_id")

    if not isinstance(email_id, str) or not email_id:
        return JsonResponse(
            {"error": "Missing email ID."},
            status=400,
        )

    try:
        message, created = process_received_email(email_id)

    except IntegrityError:
        message = EmailMessage.objects.filter(
            resend_email_id=email_id
        ).first()

        if message:
            return JsonResponse(
                {
                    "received": True,
                    "duplicate": True,
                    "message_id": message.pk,
                },
                status=200,
            )

        logger.exception(
            "Database integrity error processing email %s.",
            email_id,
        )
        return JsonResponse(
            {"error": "Database integrity error."},
            status=500,
        )

    except ResendAPIError:
        logger.exception(
            "Could not retrieve or process Resend email %s.",
            email_id,
        )
        return JsonResponse(
            {"error": "Email processing failed."},
            status=500,
        )

    except Exception:
        logger.exception(
            "Unexpected error processing Resend email %s.",
            email_id,
        )
        return JsonResponse(
            {"error": "Internal processing error."},
            status=500,
        )

    return JsonResponse(
        {
            "received": True,
            "duplicate": not created,
            "message_id": message.pk,
        },
        status=200,
    )

@staff_member_required
def download_attachment(request, attachment_id):
    """Generate a temporary private download link for an attachment."""

    attachment = EmailAttachment.objects.filter(
        pk=attachment_id
    ).first()

    if not attachment:
        raise Http404("Attachment not found.")

    try:
        download_url = create_download_url(
            attachment.storage_key,
            expires_in=300,
        )
    except Exception:
        logger.exception(
            "Could not generate download URL for attachment %s.",
            attachment_id,
        )
        return JsonResponse(
            {"error": "Could not download attachment."},
            status=503,
        )

    return HttpResponseRedirect(download_url)