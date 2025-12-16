import uuid

from django.test import TestCase

from hand.constants import HandSource
from hand.models import Hand
from user.models import Client


class TestHandModel(TestCase):
    def setUp(self):
        self.client = Client.objects.create(install_id='test-client-hand')

    def test_create_hand_with_defaults(self):
        hand = Hand.objects.create(client=self.client)

        self.assertIsInstance(hand.id, uuid.UUID)
        self.assertEqual(hand.client, self.client)
        self.assertEqual(hand.source, HandSource.CAMERA.value)
        self.assertIsNotNone(hand.created_at)
        self.assertIsNotNone(hand.updated_at)

    def test_create_hand_with_manual_source(self):
        hand = Hand.objects.create(
            client=self.client,
            source=HandSource.MANUAL.value,
        )

        self.assertEqual(hand.source, HandSource.MANUAL.value)

    def test_create_hand_with_import_source(self):
        hand = Hand.objects.create(
            client=self.client,
            source=HandSource.IMPORT.value,
        )

        self.assertEqual(hand.source, HandSource.IMPORT.value)

    def test_hand_client_relationship(self):
        hand1 = Hand.objects.create(client=self.client)
        hand2 = Hand.objects.create(client=self.client)

        self.assertEqual(self.client.hands.count(), 2)
        self.assertIn(hand1, self.client.hands.all())
        self.assertIn(hand2, self.client.hands.all())

    def test_hand_cascade_delete_with_client(self):
        Hand.objects.create(client=self.client)
        Hand.objects.create(client=self.client)

        self.assertEqual(Hand.objects.count(), 2)

        self.client.delete()

        self.assertEqual(Hand.objects.count(), 0)

    def test_uuid_is_primary_key(self):
        hand = Hand.objects.create(client=self.client)

        fetched = Hand.objects.get(pk=hand.id)
        self.assertEqual(fetched.id, hand.id)
