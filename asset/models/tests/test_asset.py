import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from asset.constants import StorageProvider, UploadStatus
from asset.models import Asset, UploadSession
from user.models import Client


class TestAssetModel(TestCase):
    def setUp(self):
        self.client = Client.objects.create(install_id='test-client-asset')
        self.upload_session = UploadSession.objects.create(client=self.client)

    def test_create_asset_with_required_fields(self):
        asset = Asset.objects.create(
            storage_provider=StorageProvider.S3.value,
            storage_key='uploads/test/image.jpg',
            mime_type='image/jpeg',
            byte_size=12345,
        )

        self.assertIsInstance(asset.id, uuid.UUID)
        self.assertEqual(asset.storage_provider, StorageProvider.S3.value)
        self.assertEqual(asset.storage_key, 'uploads/test/image.jpg')
        self.assertEqual(asset.mime_type, 'image/jpeg')
        self.assertEqual(asset.byte_size, 12345)
        self.assertTrue(asset.is_active)
        self.assertIsNone(asset.upload_session)
        self.assertIsNone(asset.checksum)
        self.assertIsNone(asset.exif_data)
        self.assertIsNone(asset.exif_captured_at)

    def test_create_asset_with_upload_session(self):
        asset = Asset.objects.create(
            upload_session=self.upload_session,
            storage_provider=StorageProvider.S3.value,
            storage_key='uploads/test/image.jpg',
            mime_type='image/jpeg',
            byte_size=12345,
        )

        self.assertEqual(asset.upload_session, self.upload_session)
        self.assertIn(asset, self.upload_session.asset.all())

    def test_create_asset_with_exif_data(self):
        exif_time = timezone.now() - timedelta(days=1)
        exif_data = {'Make': 'Apple', 'Model': 'iPhone 15'}

        asset = Asset.objects.create(
            storage_provider=StorageProvider.S3.value,
            storage_key='uploads/test/image.jpg',
            mime_type='image/jpeg',
            byte_size=12345,
            exif_data=exif_data,
            exif_captured_at=exif_time,
        )

        self.assertEqual(asset.exif_data, exif_data)
        self.assertEqual(asset.exif_captured_at, exif_time)

    def test_asset_with_checksum(self):
        asset = Asset.objects.create(
            storage_provider=StorageProvider.S3.value,
            storage_key='uploads/test/image.jpg',
            mime_type='image/jpeg',
            byte_size=12345,
            checksum='abc123def456',
        )

        self.assertEqual(asset.checksum, 'abc123def456')

    def test_asset_is_active_default_true(self):
        asset = Asset.objects.create(
            storage_provider=StorageProvider.S3.value,
            storage_key='uploads/test/image.jpg',
            mime_type='image/jpeg',
            byte_size=12345,
        )

        self.assertTrue(asset.is_active)

    def test_asset_can_be_deactivated(self):
        asset = Asset.objects.create(
            storage_provider=StorageProvider.S3.value,
            storage_key='uploads/test/image.jpg',
            mime_type='image/jpeg',
            byte_size=12345,
        )

        asset.is_active = False
        asset.save()

        asset.refresh_from_db()
        self.assertFalse(asset.is_active)

    def test_upload_session_set_null_on_delete(self):
        asset = Asset.objects.create(
            upload_session=self.upload_session,
            storage_provider=StorageProvider.S3.value,
            storage_key='uploads/test/image.jpg',
            mime_type='image/jpeg',
            byte_size=12345,
        )

        self.upload_session.delete()

        asset.refresh_from_db()
        self.assertIsNone(asset.upload_session)
