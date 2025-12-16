"""
Model loader for downloading YOLO model weights from S3.

This module handles downloading model weights from S3 at container startup.
It is designed to be called by the Celery worker before consuming tasks.
"""

import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings

from asset.exceptions import ModelDownloadError
from asset.services.s3 import download_file

logger = logging.getLogger(__name__)


def parse_s3_uri(s3_uri: str) -> tuple[str, str]:
    """
    Parse an S3 URI into bucket and key components.

    Args:
        s3_uri: S3 URI in the format s3://bucket/key/path

    Returns:
        Tuple of (bucket, key)

    Raises:
        ValueError: If the URI is not a valid S3 URI
    """
    if not s3_uri:
        raise ValueError('S3 URI cannot be empty')

    parsed = urlparse(s3_uri)

    if parsed.scheme != 's3':
        raise ValueError(
            f"Invalid S3 URI scheme: '{parsed.scheme}'. Expected 's3'",
        )

    if not parsed.netloc:
        raise ValueError('S3 URI must include a bucket name')

    bucket = parsed.netloc
    key = parsed.path.lstrip('/')

    if not key:
        raise ValueError('S3 URI must include an object key')

    return bucket, key


def get_model_local_path() -> str:
    """
    Get the local path for the model file.

    Derives path from MODEL_DIR, TILE_DETECTOR_MODEL_NAME, and
    TILE_DETECTOR_MODEL_VERSION settings.
    """
    return str(
        Path(settings.MODEL_DIR)
        / settings.TILE_DETECTOR_MODEL_NAME
        / settings.TILE_DETECTOR_MODEL_VERSION
        / 'model.pt',
    )


def ensure_model_local() -> str:
    """
    Ensure the model file exists locally, downloading from S3 if necessary.

    This function checks if the model file exists locally and has a size > 0.
    If not, it downloads the file from S3.

    Returns:
        The local path to the model file.

    Raises:
        ModelDownloadError: If download fails or required env vars are missing.
    """
    s3_uri = settings.MODEL_S3_URI

    if not s3_uri:
        raise ModelDownloadError(
            message='MODEL_S3_URI environment variable is required but not set',
        )

    local_path = get_model_local_path()
    local_file = Path(local_path)

    # Check if file already exists and has content
    if local_file.exists() and local_file.stat().st_size > 0:
        logger.info(
            f'Model already exists at {local_path} '
            f'({local_file.stat().st_size} bytes), skipping download',
        )
        return str(local_file)

    # Parse S3 URI
    try:
        bucket, key = parse_s3_uri(s3_uri)
    except ValueError as e:
        raise ModelDownloadError(message=f'Invalid S3 URI: {e}') from e

    # Create parent directories if they don't exist
    local_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        f'Starting model download from s3://{bucket}/{key} to {local_path}',
    )

    # Download from S3 (uses IAM role credentials)
    file_size = download_file(bucket, key, str(local_file))

    # Verify download
    if not local_file.exists():
        raise ModelDownloadError(
            message=f'Download completed but file not found at {local_path}',
        )

    if file_size == 0:
        local_file.unlink()
        raise ModelDownloadError(message='Downloaded file is empty')

    logger.info(
        f'Successfully downloaded model to {local_path} ({file_size} bytes)',
    )
    return str(local_file)


def load_model_on_worker_startup() -> None:
    """
    Load model on Celery worker startup.

    This function should be called from Celery's worker_init signal.
    If the download fails, it logs the error and exits with code 1
    so ECS can restart the container.
    """
    try:
        ensure_model_local()
    except ModelDownloadError as e:
        logger.error(f'Failed to load model on worker startup: {e.message}')
        sys.exit(1)
