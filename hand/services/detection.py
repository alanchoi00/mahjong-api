import uuid
from dataclasses import dataclass

from celery import current_app
from django.conf import settings
from django.db import transaction

from asset.constants import AssetRole
from asset.models import Asset, AssetRef
from hand.constants import DetectionStatus, HandSource
from hand.exceptions import (
    AssetNotActiveError,
    AssetOwnershipError,
    DetectionNotFoundError,
    DetectionOwnershipError,
)
from hand.models import Hand, HandDetection
from user.models import Client


HAND_DETECTION_TASK_NAME = 'hand.tasks.run_hand_detection'


@dataclass(frozen=True)
class TriggerDetectionResult:
    hand_id: uuid.UUID
    asset_ref_id: uuid.UUID
    hand_detection_id: uuid.UUID
    status: str


def trigger_hand_detection(
    *,
    asset_id: uuid.UUID,
    install_id: str,
    source: str = HandSource.CAMERA.value,
) -> TriggerDetectionResult:
    """
    Trigger a detection for the given asset.

    Creates Hand, AssetRef, and HandDetection, then enqueues the Celery task.
    """
    asset = Asset.objects.select_related('upload_session__client').get(
        id=asset_id,
    )

    # Validate ownership
    if (
        not asset.upload_session
        or asset.upload_session.client.install_id != install_id
    ):
        raise AssetOwnershipError(
            message=f'Asset {asset_id} does not belong to client {install_id}',
        )

    # Validate asset is active
    if not asset.is_active:
        raise AssetNotActiveError(
            message=f'Asset {asset_id} is not active. Complete upload first.',
        )

    model_version = settings.TILE_DETECTOR_MODEL_VERSION

    # Check for existing detection (idempotency)
    existing_ref = (
        AssetRef.objects.filter(
            asset=asset,
            role=AssetRole.HAND_PHOTO.value,
        )
        .select_related('owner_content_type')
        .first()
    )

    if existing_ref:
        hand_id = existing_ref.owner_id

        # Check for existing detection with same model version
        existing_detection = (
            HandDetection.objects.filter(
                hand_id=hand_id,
                model_version=model_version,
            )
            .order_by('-created_at')
            .first()
        )

        if existing_detection:
            # If not failed, return existing
            if existing_detection.status != DetectionStatus.FAILED.value:
                return TriggerDetectionResult(
                    hand_id=hand_id,
                    asset_ref_id=existing_ref.id,
                    hand_detection_id=existing_detection.id,
                    status=existing_detection.status,
                )

    # Create new detection run
    client = Client.objects.get(install_id=install_id)

    with transaction.atomic():
        hand = Hand.objects.create(
            client=client,
            source=source,
        )

        asset_ref = AssetRef.attach(
            asset=asset,
            owner=hand,
            role=AssetRole.HAND_PHOTO.value,
        )

        detection = HandDetection.objects.create(
            hand=hand,
            asset_ref=asset_ref,
            status=DetectionStatus.PENDING.value,
            model_name=settings.TILE_DETECTOR_MODEL_NAME,
            model_version=model_version,
        )

    # Enqueue Celery task via send_task to avoid importing the task module
    # This breaks the import chain that would otherwise load ML dependencies
    current_app.send_task(HAND_DETECTION_TASK_NAME, args=[str(detection.id)])

    return TriggerDetectionResult(
        hand_id=hand.id,
        asset_ref_id=asset_ref.id,
        hand_detection_id=detection.id,
        status=detection.status,
    )


def get_hand_detection(
    *,
    hand_detection_id: uuid.UUID,
    install_id: str,
) -> HandDetection:
    """
    Get a detection by ID with ownership validation.
    """
    try:
        detection = (
            HandDetection.objects.select_related(
                'hand__client',
            )
            .prefetch_related('tiles')
            .get(id=hand_detection_id)
        )
    except HandDetection.DoesNotExist:
        raise DetectionNotFoundError(
            message=f'Detection {hand_detection_id} not found.',
        ) from None

    if detection.hand.client.install_id != install_id:
        raise DetectionOwnershipError(
            message='Detection does not belong to this client.',
        )

    return detection
