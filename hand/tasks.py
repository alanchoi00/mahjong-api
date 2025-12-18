import logging
import statistics

from celery import shared_task
from django.conf import settings
from django.db import transaction

from hand.constants import DetectionStatus
from hand.models import HandDetection, DetectionTile

# NOTE: Do NOT import hand.services.inference at module level!
# The inference module imports ml.inference.model which imports ultralytics/cv2.
# These ML dependencies should only load inside the Celery worker at task runtime.

logger = logging.getLogger(__name__)


def _area_xyxy(x1: int, y1: int, x2: int, y2: int) -> float:
    w = max(0, x2 - x1)
    h = max(0, y2 - y1)
    return float(w * h)


def iou_xyxy(a: DetectionTile, b: DetectionTile) -> float:
    ix1: int = max(a.x1, b.x1)
    iy1 = max(a.y1, b.y1)
    ix2 = min(a.x2, b.x2)
    iy2 = min(a.y2, b.y2)

    inter = _area_xyxy(ix1, iy1, ix2, iy2)
    if inter <= 0.0:
        return 0.0

    area_a = _area_xyxy(a.x1, a.y1, a.x2, a.y2)
    area_b = _area_xyxy(b.x1, b.y1, b.x2, b.y2)
    union = area_a + area_b - inter
    return inter / union if union > 0.0 else 0.0


def _conf(x: DetectionTile) -> float:
    # normalize confidence to float once, consistently
    return float(x.confidence)


def nms_by_iou_keep_best(
    tiles: list[DetectionTile],
    *,
    iou_threshold=0.5,
) -> list[DetectionTile]:
    """
    Greedy NMS (class-agnostic):
    - Sort by confidence desc
    - Keep a tile if IoU with any kept tile <= threshold
    """
    tiles_sorted = sorted(tiles, key=_conf, reverse=True)
    kept: list[DetectionTile] = []

    for t in tiles_sorted:
        suppress: bool = False
        for k in kept:
            if iou_xyxy(t, k) > iou_threshold:
                suppress = True
                break
        if not suppress:
            kept.append(t)

    return kept


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

    if detection.status not in (
        DetectionStatus.PENDING.value,
        DetectionStatus.RUNNING.value,
    ):
        logger.warning(
            f'Detection {hand_detection_id} already in status '
            f'{detection.status}, skipping',
        )
        return

    detection.status = DetectionStatus.RUNNING.value
    detection.save(update_fields=['status', 'updated_at'])

    try:
        # Lazy import to avoid loading ML dependencies at module import time
        # This ensures Django startup/migrations don't import ultralytics/cv2
        from hand.services.inference import run_inference

        threshold = settings.DETECTION_CONFIDENCE_THRESHOLD
        if threshold is None:
            raise ValueError(
                'DETECTION_CONFIDENCE_THRESHOLD not set in settings',
            )

        storage_key = detection.asset_ref.asset.storage_key

        result = run_inference(
            storage_key=storage_key,
            model_name=detection.model_name,
            model_version=detection.model_version,
        )

        # Filter tiles by threshold
        kept_tiles = [
            t for t in result.tiles if float(t.confidence) >= threshold
        ]

        if kept_tiles:
            confidence_overall = statistics.mean(
                float(t.confidence) for t in kept_tiles
            )
        else:
            confidence_overall = 0.0

        with transaction.atomic():
            if not kept_tiles:
                detection.status = DetectionStatus.FAILED.value
                detection.error_code = 'NoTilesAboveThreshold'
                detection.error_message = (
                    'No detected tiles met confidence threshold '
                    f'({threshold}).'
                )
                detection.confidence_overall = confidence_overall
                detection.save(
                    update_fields=[
                        'confidence_overall',
                        'status',
                        'error_code',
                        'error_message',
                        'updated_at',
                    ],
                )
                logger.info(
                    f'Detection {hand_detection_id} failed: 0 tiles >= {threshold}',
                )
                return

            detection.confidence_overall = confidence_overall
            detection.status = DetectionStatus.SUCCEEDED.value
            detection.save(
                update_fields=[
                    'confidence_overall',
                    'status',
                    'updated_at',
                ],
            )

            DetectionTile.objects.bulk_create(
                [
                    DetectionTile(
                        detection=detection,
                        tile_code=tile.tile_code,
                        x1=tile.x1,
                        y1=tile.y1,
                        x2=tile.x2,
                        y2=tile.y2,
                        confidence=tile.confidence,
                    )
                    for tile in kept_tiles
                ],
            )

        logger.info(
            f'Detection {hand_detection_id} succeeded with '
            f'{len(kept_tiles)} tiles (threshold={threshold})',
        )

    except Exception as e:
        logger.exception(f'Detection {hand_detection_id} failed: {e}')

        detection.status = DetectionStatus.FAILED.value
        detection.error_code = type(e).__name__
        detection.error_message = str(e)[:1000]
        detection.save(
            update_fields=[
                'status',
                'error_code',
                'error_message',
                'updated_at',
            ],
        )
