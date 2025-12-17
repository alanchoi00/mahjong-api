import uuid
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction

from asset.constants import (
    ALLOWED_IMAGE_MIMES,
    StorageProvider,
    UploadPurpose,
    UploadStatus,
)
from asset.exceptions import (
    InvalidFileTypeError,
    InvalidUploadSessionStateError,
    UploadNotCompleteError,
)
from asset.models import Asset, UploadSession
from asset.services.s3 import generate_presigned_put_url, head_object
from user.models import Client


@dataclass(frozen=True)
class PresignResult:
    upload_session_id: uuid.UUID
    asset_id: uuid.UUID
    presigned_url: str
    storage_key: str


@dataclass(frozen=True)
class CompleteResult:
    upload_session_id: uuid.UUID
    asset_id: uuid.UUID
    is_active: bool
    byte_size: int
    checksum: str | None


def validate_content_type(content_type: str) -> None:
    if content_type not in ALLOWED_IMAGE_MIMES:
        raise InvalidFileTypeError(
            message=(
                f'Invalid content type: {content_type}. '
                f'Allowed types: {", ".join(sorted(ALLOWED_IMAGE_MIMES))}'
            ),
        )


def generate_storage_key(
    client_id: str,
    asset_id: uuid.UUID,
    content_type: str,
    purpose: str,
) -> str:
    extension = content_type.split('/')[-1]
    if extension == 'jpeg':
        extension = 'jpg'
    return f'uploads/{client_id}/{purpose}/{asset_id}.{extension}'


def create_presigned_upload(
    *,
    install_id: str,
    content_type: str,
    purpose: str = UploadPurpose.HAND_PHOTO.value,
) -> PresignResult:
    """
    Generate a presigned PUT URL for uploading an asset and create the
    corresponding UploadSession and Asset in the PRESIGNED state.

    Args:
        install_id: Install identifier for the owning client.
        content_type: MIME type of the file (must be in ALLOWED_IMAGE_MIMES).
        purpose: Purpose of the upload (defaults to HAND_PHOTO).

    Returns:
        PresignResult with upload_session_id, asset_id, presigned_url,
        and storage_key.

    Raises:
        InvalidFileTypeError: If content_type is not allowed.
        Client.DoesNotExist: If no client exists with the provided install_id.
    """
    validate_content_type(content_type)
    client = Client.objects.get(install_id=install_id)

    asset_id = uuid.uuid4()
    storage_key = generate_storage_key(
        client.install_id,
        asset_id,
        content_type,
        purpose,
    )
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    presigned_url = generate_presigned_put_url(
        bucket_name=bucket_name,
        object_name=storage_key,
        content_type=content_type,
    )

    with transaction.atomic():
        upload_session = UploadSession.objects.create(
            client=client,
            status=UploadStatus.PRESIGNED.value,
            purpose=purpose,
        )

        Asset.objects.create(
            id=asset_id,
            upload_session=upload_session,
            storage_provider=StorageProvider.S3.value,
            storage_key=storage_key,
            mime_type=content_type,
            byte_size=0,
            is_active=False,
        )

    return PresignResult(
        upload_session_id=upload_session.id,
        asset_id=asset_id,
        presigned_url=presigned_url,
        storage_key=storage_key,
    )


def complete_upload(
    *,
    asset_id: uuid.UUID,
    install_id: str,
) -> CompleteResult:
    """
    Complete an upload by validating the file exists in storage and updating
    asset metadata.

    Does NOT create Hand or AssetRef - that happens when detection is triggered.

    Args:
        asset_id: The asset ID to complete.
        install_id: The install_id for ownership validation.

    Returns:
        CompleteResult with asset metadata.

    Raises:
        Asset.DoesNotExist: If asset not found or ownership mismatch.
        InvalidUploadSessionStateError: If session not in PRESIGNED state.
        UploadNotCompleteError: If file not found in storage.
    """
    asset = Asset.objects.select_related('upload_session__client').get(
        id=asset_id,
        upload_session__client__install_id=install_id,
    )
    upload_session = asset.upload_session

    if upload_session.status != UploadStatus.PRESIGNED.value:
        raise InvalidUploadSessionStateError(
            message=(
                f'Upload session is in state "{upload_session.status}", '
                f'expected "{UploadStatus.PRESIGNED.value}"'
            ),
        )

    metadata = head_object(
        bucket_name=settings.AWS_STORAGE_BUCKET_NAME,
        object_name=asset.storage_key,
    )

    if metadata is None:
        raise UploadNotCompleteError(
            message=f'File not found in storage: {asset.storage_key}',
        )

    with transaction.atomic():
        asset.byte_size = metadata.content_length
        asset.checksum = metadata.etag
        asset.is_active = True
        asset.save(
            update_fields=['byte_size', 'checksum', 'is_active', 'updated_at'],
        )

        upload_session.status = UploadStatus.COMPLETED.value
        upload_session.save(update_fields=['status', 'updated_at'])

    return CompleteResult(
        upload_session_id=upload_session.id,
        asset_id=asset.id,
        is_active=asset.is_active,
        byte_size=asset.byte_size,
        checksum=asset.checksum,
    )
