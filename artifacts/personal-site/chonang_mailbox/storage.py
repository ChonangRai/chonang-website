
"""Private attachment storage using Cloudflare R2."""

import boto3
from botocore.config import Config
from django.conf import settings


def get_r2_client():
    """Create an S3-compatible client for Cloudflare R2."""
    config = settings.R2_STORAGE

    required = (
        "endpoint_url",
        "access_key_id",
        "secret_access_key",
        "bucket_name",
    )
    missing = [key for key in required if not config.get(key)]

    if missing:
        raise RuntimeError(
            "R2 configuration is incomplete. Missing: "
            + ", ".join(missing)
        )

    return boto3.client(
        "s3",
        endpoint_url=config["endpoint_url"],
        aws_access_key_id=config["access_key_id"],
        aws_secret_access_key=config["secret_access_key"],
        region_name=config["region_name"],
        config=Config(signature_version="s3v4"),
    )


def upload_attachment(file_object, object_key, content_type):
    """Upload an attachment to the private R2 bucket."""
    client = get_r2_client()
    config = settings.R2_STORAGE

    client.upload_fileobj(
        file_object,
        config["bucket_name"],
        object_key,
        ExtraArgs={"ContentType": content_type},
    )

    return object_key


def create_download_url(object_key, expires_in=300):
    """Create a temporary private download URL."""
    client = get_r2_client()
    config = settings.R2_STORAGE

    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": config["bucket_name"],
            "Key": object_key,
        },
        ExpiresIn=expires_in,
    )

def delete_attachment(object_key):
    """Delete an attachment from the private R2 bucket."""

    client = get_r2_client()
    config = settings.R2_STORAGE

    client.delete_object(
        Bucket=config["bucket_name"],
        Key=object_key,
    )
