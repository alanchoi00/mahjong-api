import uuid

from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from core.models import TimeStampedModel
from asset.models.asset import Asset


class AssetRef(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='refs',
    )

    owner_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    owner_id = models.UUIDField()
    owner = GenericForeignKey('owner_content_type', 'owner_id')

    role = models.CharField(max_length=64, blank=True, default='')
    ordering = models.IntegerField(default=0)

    captured_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['owner_content_type', 'owner_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['captured_at']),
        ]

    @classmethod
    def attach(
        cls,
        *,
        asset: Asset,
        owner: models.Model,
        role: str = '',
        captured_at: timezone.datetime | None = None,
    ) -> 'AssetRef':
        if captured_at is None:
            captured_at = asset.exif_captured_at or timezone.now()

        return cls.objects.create(
            asset=asset,
            owner_content_type=ContentType.objects.get_for_model(
                owner,
                for_concrete_model=False,
            ),
            owner_id=owner.id,
            role=role,
            captured_at=captured_at,
        )
