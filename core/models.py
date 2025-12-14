from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
    )
    updated_at = models.DateTimeField(
        default=timezone.now,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)
