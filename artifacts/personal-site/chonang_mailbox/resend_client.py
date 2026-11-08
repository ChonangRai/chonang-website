"""Small HTTP client for the Resend Receiving API."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
    urlopen,
)
from urllib.parse import quote, urlparse

from django.conf import settings


RESEND_API_BASE = "https://api.resend.com"

class _NoRedirectHandler(HTTPRedirectHandler):
    """Prevent attachment downloads from following redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class ResendAPIError(Exception):
    """Raised when a Resend API request fails."""


def _get_api_key():
    api_key = settings.RESEND_API_KEY

    if not api_key:
        raise ResendAPIError("Resend API key is not configured.")

    return api_key


def _get_json(path):
    """Make an authenticated GET request and return its JSON response."""

    request = Request(
        f"{RESEND_API_BASE}{path}",
        headers={
            "Authorization": f"Bearer {_get_api_key()}",
            "Accept": "application/json",
            "User-Agent": "chonang-mail/1.0",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")

        try:
            error_data = json.loads(error_body)
            detail = (
                error_data.get("message")
                or error_data.get("error")
                or error_data.get("name")
            )
        except (json.JSONDecodeError, AttributeError):
            detail = None

        if not isinstance(detail, str):
            detail = "No additional details returned."

        raise ResendAPIError(
            f"Resend returned HTTP {exc.code}: {detail[:300]}"
        ) from exc

    except (URLError, TimeoutError) as exc:
        raise ResendAPIError(
            "Could not connect to Resend."
        ) from exc

    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ResendAPIError(
            "Resend returned an invalid response."
        ) from exc


def get_received_email(email_id):
    """Retrieve the complete content of a received email."""

    safe_email_id = quote(email_id, safe="")

    return _get_json(
        f"/emails/receiving/{safe_email_id}"
    )

def list_received_attachments(email_id):
    """Retrieve attachment metadata and temporary download URLs."""

    safe_email_id = quote(email_id, safe="")

    response = _get_json(
        f"/emails/receiving/{safe_email_id}/attachments"
    )

    if not isinstance(response, dict):
        raise ResendAPIError("Invalid attachment response from Resend.")

    attachments = response.get("data", [])

    if not isinstance(attachments, list):
        raise ResendAPIError("Invalid attachment list from Resend.")

    return attachments

def download_received_attachment(download_url, max_bytes=20 * 1024 * 1024):
    """Download an attachment with a 20 MB size limit."""

    parsed_url = urlparse(download_url)

    if (
        parsed_url.scheme != "https"
        or not parsed_url.netloc
        or parsed_url.username
        or parsed_url.password
    ):
        raise ResendAPIError("Invalid attachment download URL.")

    request = Request(
        download_url,
        headers={"Accept": "application/octet-stream"},
        method="GET",
    )

    try:
        opener = build_opener(_NoRedirectHandler)

        with opener.open(request, timeout=30) as response:
            content_length = response.headers.get("Content-Length")

            if content_length and int(content_length) > max_bytes:
                raise ResendAPIError("Attachment exceeds the 20 MB limit.")

            chunks = []
            total_size = 0

            while True:
                chunk = response.read(64 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > max_bytes:
                    raise ResendAPIError(
                        "Attachment exceeds the 20 MB limit."
                    )

                chunks.append(chunk)

            return b"".join(chunks)

    except HTTPError as exc:
        raise ResendAPIError(
            f"Attachment download failed with HTTP {exc.code}."
        ) from exc

    except (URLError, TimeoutError) as exc:
        raise ResendAPIError(
            "Could not download the attachment."
        ) from exc
