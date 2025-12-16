import uuid

from django.db import models

from core.models import TimeStampedModel


class Asset(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    upload_session = models.ForeignKey(
        'asset.UploadSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset',
    )

    is_active = models.BooleanField(default=True)

    storage_provider = models.CharField(max_length=32)
    storage_key = models.CharField(max_length=512)

    mime_type = models.CharField(max_length=127)
    byte_size = models.BigIntegerField()

    checksum = models.CharField(max_length=128, null=True, blank=True)

    # EXIF is naturally flexible, so JSONField is appropriate here.
    exif_data = models.JSONField(null=True, blank=True)
    exif_captured_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['storage_provider', 'storage_key']),
            models.Index(fields=['checksum']),
            models.Index(fields=['created_at']),
            models.Index(fields=['exif_captured_at']),
            models.Index(fields=['is_active']),
        ]
