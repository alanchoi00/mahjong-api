import uuid

from django.db import models

from core.models import TimeStampedModel
from user.models import Client
from hand.constants import HandSource


class Hand(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='hands',
    )

    source = models.CharField(
        max_length=32,
        choices=HandSource.choices(),
        default=HandSource.CAMERA.value,
    )

    class Meta:
        indexes = [
            models.Index(fields=['client', 'created_at']),
            models.Index(fields=['created_at']),
        ]
