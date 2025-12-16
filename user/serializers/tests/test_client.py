from django.test import TestCase
from django.utils import timezone

from user.serializers import (
    ClientResponseSerializer,
    IdentifyRequestSerializer,
)


class TestIdentifyRequestSerializer(TestCase):
    def test_valid_with_install_id_only(self):
        serializer = IdentifyRequestSerializer(data={'install_id': 'test-123'})

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['install_id'], 'test-123')
        self.assertEqual(serializer.validated_data['label'], '')

    def test_valid_with_install_id_and_label(self):
        serializer = IdentifyRequestSerializer(
            data={'install_id': 'test-456', 'label': 'My Device'},
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['label'], 'My Device')

    def test_invalid_without_install_id(self):
        serializer = IdentifyRequestSerializer(data={})

        self.assertFalse(serializer.is_valid())
        self.assertIn('install_id', serializer.errors)

    def test_invalid_with_empty_install_id(self):
        serializer = IdentifyRequestSerializer(data={'install_id': ''})

        self.assertFalse(serializer.is_valid())
        self.assertIn('install_id', serializer.errors)

    def test_allows_blank_label(self):
        serializer = IdentifyRequestSerializer(
            data={'install_id': 'test-789', 'label': ''},
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['label'], '')

    def test_install_id_max_length(self):
        serializer = IdentifyRequestSerializer(data={'install_id': 'x' * 65})

        self.assertFalse(serializer.is_valid())
        self.assertIn('install_id', serializer.errors)


class TestClientResponseSerializer(TestCase):
    def test_serializes_client_data(self):
        now = timezone.now()
        data = {
            'install_id': 'client-123',
            'label': 'Test Device',
            'created_at': now,
            'last_seen_at': now,
        }

        serializer = ClientResponseSerializer(instance=data)

        self.assertEqual(serializer.data['install_id'], 'client-123')
        self.assertEqual(serializer.data['label'], 'Test Device')
        self.assertIn('created_at', serializer.data)
        self.assertIn('last_seen_at', serializer.data)
