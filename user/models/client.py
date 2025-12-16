from django.utils import timezone
from django.db import models


class Client(models.Model):
    """
    Anonymous install identity.

    - Created on first app launch (client-side).
    - Sent on every request as X-Install-Id or in the payload.
    - Lets you support:
        - per-install history
        - per-install rulesets
        - later: upgrade to real auth by linking a user account to this install_id
    """

    install_id = models.CharField(
        primary_key=True,
        max_length=64,
    )

    label = models.CharField(
        max_length=120,
        blank=True,
        default='',
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
    )

    last_seen_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    def touch(self, *, when: timezone.datetime | None = None) -> None:
        """
        Update last_seen_at without changing other fields.
        Call this whenever the app pings /identify or performs any request.
        """
        self.last_seen_at = when or timezone.now()
        self.save(update_fields=['last_seen_at'])
