from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from user.models import Client


class TestClientModel(TestCase):
    def test_create_client(self):
        client = Client.objects.create(install_id='test-install-123')

        self.assertEqual(client.install_id, 'test-install-123')
        self.assertEqual(client.label, '')
        self.assertIsNotNone(client.created_at)
        self.assertIsNotNone(client.last_seen_at)

    def test_create_client_with_label(self):
        client = Client.objects.create(
            install_id='test-install-456',
            label='Test Device',
        )

        self.assertEqual(client.label, 'Test Device')

    def test_touch_updates_last_seen_at(self):
        client = Client.objects.create(install_id='touch-test')
        original_last_seen = client.last_seen_at

        future_time = timezone.now() + timedelta(hours=1)
        client.touch(when=future_time)

        client.refresh_from_db()
        self.assertEqual(client.last_seen_at, future_time)
        self.assertNotEqual(client.last_seen_at, original_last_seen)

    def test_touch_without_when_uses_current_time(self):
        client = Client.objects.create(install_id='touch-test-2')
        old_time = client.last_seen_at - timedelta(hours=1)
        client.last_seen_at = old_time
        client.save()

        client.touch()

        client.refresh_from_db()
        self.assertGreater(client.last_seen_at, old_time)

    def test_install_id_is_primary_key(self):
        client = Client.objects.create(install_id='pk-test')

        self.assertEqual(client.pk, 'pk-test')

        fetched = Client.objects.get(pk='pk-test')
        self.assertEqual(fetched.install_id, 'pk-test')
