import uuid
from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from asset.constants import StorageProvider
from asset.models import Asset, AssetRef
from hand.models import Hand
from user.models import Client


class TestAssetRefModel(TestCase):
    def setUp(self):
        self.client = Client.objects.create(install_id='test-client-ref')
        self.hand = Hand.objects.create(client=self.client)
        self.asset = Asset.objects.create(
            storage_provider=StorageProvider.S3.value,
            storage_key='uploads/test/image.jpg',
            mime_type='image/jpeg',
            byte_size=12345,
        )

    def test_create_asset_ref_directly(self):
        from django.contrib.contenttypes.models import ContentType

        ref = AssetRef.objects.create(
            asset=self.asset,
            owner_content_type=ContentType.objects.get_for_model(Hand),
            owner_id=self.hand.id,
        )

        self.assertIsInstance(ref.id, uuid.UUID)
        self.assertEqual(ref.asset, self.asset)
        self.assertEqual(ref.owner, self.hand)
        self.assertEqual(ref.role, '')
        self.assertEqual(ref.ordering, 0)

    def test_attach_creates_asset_ref(self):
        ref = AssetRef.attach(asset=self.asset, owner=self.hand)

        self.assertEqual(ref.asset, self.asset)
        self.assertEqual(ref.owner, self.hand)
        self.assertIsNotNone(ref.captured_at)

    def test_attach_with_role(self):
        ref = AssetRef.attach(
            asset=self.asset,
            owner=self.hand,
            role='primary',
        )

        self.assertEqual(ref.role, 'primary')

    def test_attach_with_captured_at(self):
        captured_time = timezone.now() - timedelta(hours=2)

        ref = AssetRef.attach(
            asset=self.asset,
            owner=self.hand,
            captured_at=captured_time,
        )

        self.assertEqual(ref.captured_at, captured_time)

    def test_attach_uses_exif_captured_at_when_no_captured_at_provided(self):
        exif_time = timezone.now() - timedelta(days=1)
        asset_with_exif = Asset.objects.create(
            storage_provider=StorageProvider.S3.value,
            storage_key='uploads/test/exif.jpg',
            mime_type='image/jpeg',
            byte_size=12345,
            exif_captured_at=exif_time,
        )

        ref = AssetRef.attach(asset=asset_with_exif, owner=self.hand)

        self.assertEqual(ref.captured_at, exif_time)

    def test_asset_ref_protects_asset_on_delete(self):
        AssetRef.attach(asset=self.asset, owner=self.hand)

        with self.assertRaises(IntegrityError):
            self.asset.delete()

    def test_asset_can_have_multiple_refs(self):
        hand2 = Hand.objects.create(client=self.client)

        ref1 = AssetRef.attach(asset=self.asset, owner=self.hand)
        ref2 = AssetRef.attach(asset=self.asset, owner=hand2)

        self.assertEqual(self.asset.refs.count(), 2)
        self.assertIn(ref1, self.asset.refs.all())
        self.assertIn(ref2, self.asset.refs.all())

    def test_owner_generic_relation(self):
        ref = AssetRef.attach(asset=self.asset, owner=self.hand)

        self.assertEqual(ref.owner, self.hand)
        self.assertEqual(ref.owner_id, self.hand.id)
