import uuid

from django.db import models

from core.models import TimeStampedModel
from hand.constants import DetectionStatus
from hand.models.hand import Hand
from asset.models import AssetRef


class HandDetection(TimeStampedModel):
    """
    Represents a single detection run for a hand.

    Each detection run is tied to a specific Hand and AssetRef (the image
    being analyzed). The detection is processed asynchronously by a Celery
    worker.

    Status lifecycle:
        pending -> running -> succeeded | failed
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    hand = models.ForeignKey(
        Hand,
        on_delete=models.CASCADE,
        related_name='detections',
    )

    asset_ref = models.ForeignKey(
        AssetRef,
        on_delete=models.PROTECT,
        related_name='detections',
    )

    status = models.CharField(
        max_length=32,
        choices=DetectionStatus.choices(),
        default=DetectionStatus.PENDING.value,
    )

    # Model identification
    model_name = models.CharField(max_length=128, blank=True, default='')
    model_version = models.CharField(max_length=64, blank=True, default='')

    # Aggregate confidence score (0.0 - 1.0)
    confidence_overall = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
    )

    # Error tracking for failed detections
    error_code = models.CharField(max_length=64, blank=True, default='')
    error_message = models.TextField(blank=True, default='')

    class Meta:
        indexes = [
            models.Index(fields=['hand', 'created_at']),
            models.Index(fields=['asset_ref']),
            models.Index(fields=['status']),
            models.Index(fields=['model_version', 'status']),
        ]
        ordering = ['-created_at']
