from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from user.exceptions import ClientNotFound
from user.models import Client
from user.services import delete_client, get_client, identify_client


class TestIdentifyClient(TestCase):
    def test_creates_new_client(self):
        client = identify_client(install_id='new-install-123')

        self.assertEqual(client.install_id, 'new-install-123')
        self.assertEqual(client.label, '')
        self.assertIsNotNone(client.created_at)
        self.assertIsNotNone(client.last_seen_at)

    def test_creates_new_client_with_label(self):
        client = identify_client(
            install_id='new-install-456',
            label='My iPhone',
        )

        self.assertEqual(client.label, 'My iPhone')

    def test_returns_existing_client(self):
        existing = Client.objects.create(install_id='existing-123')

        client = identify_client(install_id='existing-123')

        self.assertEqual(client.install_id, existing.install_id)
        self.assertEqual(Client.objects.count(), 1)

    def test_updates_last_seen_at_for_existing_client(self):
        old_time = timezone.now() - timedelta(hours=1)
        existing = Client.objects.create(install_id='existing-456')
        existing.last_seen_at = old_time
        existing.save()

        client = identify_client(install_id='existing-456')

        self.assertGreater(client.last_seen_at, old_time)

    def test_updates_label_for_existing_client(self):
        Client.objects.create(install_id='existing-789', label='Old Label')

        client = identify_client(install_id='existing-789', label='New Label')

        self.assertEqual(client.label, 'New Label')

    def test_does_not_update_label_if_empty(self):
        Client.objects.create(install_id='existing-abc', label='Keep This')

        client = identify_client(install_id='existing-abc', label='')

        self.assertEqual(client.label, 'Keep This')


class TestGetClient(TestCase):
    def test_returns_client(self):
        Client.objects.create(install_id='get-test-123')

        client = get_client(install_id='get-test-123')

        self.assertEqual(client.install_id, 'get-test-123')

    def test_raises_for_nonexistent_client(self):
        with self.assertRaises(ClientNotFound):
            get_client(install_id='nonexistent')


class TestDeleteClient(TestCase):
    def test_deletes_client(self):
        Client.objects.create(install_id='delete-test-123')

        delete_client(install_id='delete-test-123')

        self.assertEqual(Client.objects.count(), 0)

    def test_raises_for_nonexistent_client(self):
        with self.assertRaises(ClientNotFound):
            delete_client(install_id='nonexistent')
