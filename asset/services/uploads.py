import uuid
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction

from hand.constants import HandSource
from hand.models import Hand
from asset.constants import (
    ALLOWED_IMAGE_MIMES,
    AssetRole,
    StorageProvider,
    UploadPurpose,
    UploadStatus,
)
from asset.exceptions import (
    InvalidFileTypeError,
    InvalidUploadSessionStateError,
    UploadNotCompleteError,
)
from asset.models import Asset, AssetRef, UploadSession
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
    hand_id: uuid.UUID
    asset_ref_id: uuid.UUID


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
) -> str:
    extension = content_type.split('/')[-1]
    if extension == 'jpeg':
        extension = 'jpg'
    return f'uploads/{client_id}/{asset_id}.{extension}'


def create_presigned_upload(
    *,
    install_id: str,
    content_type: str,
    purpose: str = UploadPurpose.HAND_PHOTO.value,
) -> PresignResult:
    validate_content_type(content_type)
    client = Client.objects.get(install_id=install_id)

    asset_id = uuid.uuid4()
    storage_key = generate_storage_key(
        client.install_id,
        asset_id,
        content_type,
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
    upload_session_id: uuid.UUID,
    asset_id: uuid.UUID,
    captured_at: str | None = None,
) -> CompleteResult:
    upload_session = UploadSession.objects.get(id=upload_session_id)

    if upload_session.status != UploadStatus.PRESIGNED.value:
        raise InvalidUploadSessionStateError(
            message=(
                f'Upload session is in state "{upload_session.status}", '
                f'expected "{UploadStatus.PRESIGNED.value}"'
            ),
        )

    asset = Asset.objects.get(id=asset_id, upload_session=upload_session)

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

        hand = Hand.objects.create(
            client=upload_session.client,
            source=HandSource.CAMERA.value,
        )

        asset_ref = AssetRef.attach(
            asset=asset,
            owner=hand,
            role=AssetRole.HAND_PHOTO.value,
            captured_at=captured_at,
        )

    return CompleteResult(
        upload_session_id=upload_session.id,
        asset_id=asset.id,
        hand_id=hand.id,
        asset_ref_id=asset_ref.id,
    )
