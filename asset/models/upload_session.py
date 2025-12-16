import uuid

from django.db import models

from core.models import TimeStampedModel
from asset.constants import UploadStatus
from user.models import Client


class UploadSession(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='upload_sessions',
    )
    status = models.CharField(
        choices=UploadStatus.choices(),
        max_length=32,
        default=UploadStatus.CREATED.value,
    )
    purpose = models.CharField(max_length=256, blank=True, default='')

    class Meta:
        indexes = [
            models.Index(fields=['client', 'created_at']),
            models.Index(fields=['status']),
        ]
