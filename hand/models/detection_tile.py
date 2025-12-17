import uuid

from django.db import models

from core.models import TimeStampedModel
from hand.models.hand_detection import HandDetection
from hand.tiles import TileCode


class DetectionTile(TimeStampedModel):
    """
    Represents a single tile detected within a HandDetection run.

    Each tile has:
    - A canonical tile_code (e.g., '1W', 'RD', 'EW')
    - Bounding box coordinates (x1, y1, x2, y2) in pixels
    - Per-tile confidence score
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    detection = models.ForeignKey(
        HandDetection,
        on_delete=models.CASCADE,
        related_name='tiles',
    )

    tile_code = models.CharField(max_length=8, choices=TileCode.choices())

    # Bounding box coordinates (in pixels)
    x1 = models.IntegerField()
    y1 = models.IntegerField()
    x2 = models.IntegerField()
    y2 = models.IntegerField()

    confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
    )

    class Meta:
        indexes = [
            models.Index(fields=['detection']),
            models.Index(fields=['tile_code']),
        ]
        ordering = ['x1']  # Order by horizontal position
