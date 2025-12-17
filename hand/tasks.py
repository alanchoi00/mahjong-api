import logging

from celery import shared_task
from django.db import transaction

from hand.constants import DetectionStatus
from hand.models import HandDetection, DetectionTile

# NOTE: Do NOT import hand.services.inference at module level!
# The inference module imports ml.inference.model which imports ultralytics/cv2.
# These ML dependencies should only load inside the Celery worker at task runtime.

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_hand_detection(self, hand_detection_id: str):
    """
    Run tile detection on a hand image.

    Input is hand_detection_id (not hand_id) because:
    - Detection is the unit of work (same hand can have multiple detections)
    - All needed context (model version, asset ref) is on the detection
    - Enables proper idempotency checks

    This task does NOT use autoretry because failures should be persisted
    as detection status, not retried automatically.
    """
    try:
        detection = HandDetection.objects.select_related(
            'asset_ref__asset',
        ).get(id=hand_detection_id)
    except HandDetection.DoesNotExist:
        logger.error(f'HandDetection {hand_detection_id} not found')
        return

    # Guard against duplicate runs
    if detection.status not in (
        DetectionStatus.PENDING.value,
        DetectionStatus.RUNNING.value,
    ):
        logger.warning(
            f'Detection {hand_detection_id} already in status '
            f'{detection.status}, skipping',
        )
        return

    # Mark as running
    detection.status = DetectionStatus.RUNNING.value
    detection.save(update_fields=['status', 'updated_at'])

    try:
        # Lazy import to avoid loading ML dependencies at module import time
        # This ensures Django startup/migrations don't import ultralytics/cv2
        from hand.services.inference import run_inference

        storage_key = detection.asset_ref.asset.storage_key

        result = run_inference(
            storage_key=storage_key,
            model_name=detection.model_name,
            model_version=detection.model_version,
        )

        # Persist results atomically
        with transaction.atomic():
            detection.confidence_overall = result.confidence_overall
            detection.status = DetectionStatus.SUCCEEDED.value
            detection.save(
                update_fields=[
                    'confidence_overall',
                    'status',
                    'updated_at',
                ],
            )

            # Create DetectionTile rows
            tiles_to_create = [
                DetectionTile(
                    detection=detection,
                    tile_code=tile.tile_code,
                    x1=tile.x1,
                    y1=tile.y1,
                    x2=tile.x2,
                    y2=tile.y2,
                    confidence=tile.confidence,
                )
                for tile in result.tiles
            ]
            DetectionTile.objects.bulk_create(tiles_to_create)

        logger.info(
            f'Detection {hand_detection_id} succeeded with '
            f'{len(result.tiles)} tiles',
        )

    except Exception as e:
        logger.exception(f'Detection {hand_detection_id} failed: {e}')

        # Mark as failed with error details
        detection.status = DetectionStatus.FAILED.value
        detection.error_code = type(e).__name__
        detection.error_message = str(e)[:1000]  # Truncate long messages
        detection.save(
            update_fields=[
                'status',
                'error_code',
                'error_message',
                'updated_at',
            ],
        )
