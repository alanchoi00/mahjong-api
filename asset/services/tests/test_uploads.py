import uuid
from unittest.mock import patch

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from asset.constants import UploadStatus
from asset.exceptions import (
    InvalidFileTypeError,
    InvalidUploadSessionStateError,
    UploadNotCompleteError,
)
from asset.factories import AssetFactory, ClientFactory, UploadSessionFactory
from asset.models import Asset, UploadSession
from asset.services.s3 import S3ObjectMetadata
from asset.services.uploads import (
    complete_upload,
    create_presigned_upload,
    generate_storage_key,
    validate_content_type,
)
from hand.models import Hand


class TestValidateContentType(TestCase):
    def test_valid_jpeg(self):
        validate_content_type('image/jpeg')

    def test_valid_png(self):
        validate_content_type('image/png')

    def test_valid_webp(self):
        validate_content_type('image/webp')

    def test_invalid_pdf_raises_error(self):
        with self.assertRaises(InvalidFileTypeError):
            validate_content_type('application/pdf')

    def test_invalid_text_raises_error(self):
        with self.assertRaises(InvalidFileTypeError):
            validate_content_type('text/plain')


class TestGenerateStorageKey(TestCase):
    def test_jpeg_extension_converted_to_jpg(self):
        asset_id = uuid.uuid4()
        key = generate_storage_key('client123', asset_id, 'image/jpeg')
        self.assertEqual(key, f'uploads/client123/{asset_id}.jpg')

    def test_png_extension(self):
        asset_id = uuid.uuid4()
        key = generate_storage_key('client123', asset_id, 'image/png')
        self.assertEqual(key, f'uploads/client123/{asset_id}.png')

    def test_webp_extension(self):
        asset_id = uuid.uuid4()
        key = generate_storage_key('client123', asset_id, 'image/webp')
        self.assertEqual(key, f'uploads/client123/{asset_id}.webp')


class TestCreatePresignedUpload(TestCase):
    @patch('asset.services.uploads.generate_presigned_put_url')
    def test_creates_session_and_asset(self, mock_presign):
        mock_presign.return_value = 'https://s3.example.com/presigned'
        client = ClientFactory()

        result = create_presigned_upload(
            install_id=client.install_id,
            content_type='image/jpeg',
            purpose='hand_photo',
        )

        self.assertIsNotNone(result.upload_session_id)
        self.assertIsNotNone(result.asset_id)
        self.assertEqual(
            result.presigned_url,
            'https://s3.example.com/presigned',
        )

        session = UploadSession.objects.get(id=result.upload_session_id)
        self.assertEqual(session.status, UploadStatus.PRESIGNED.value)
        self.assertEqual(session.client, client)

        asset = Asset.objects.get(id=result.asset_id)
        self.assertEqual(asset.upload_session, session)
        self.assertFalse(asset.is_active)

    @patch('asset.services.uploads.generate_presigned_put_url')
    def test_invalid_content_type_raises_error(self, mock_presign):
        client = ClientFactory()

        with self.assertRaises(InvalidFileTypeError):
            create_presigned_upload(
                install_id=client.install_id,
                content_type='application/pdf',
            )

        mock_presign.assert_not_called()

    @patch('asset.services.uploads.generate_presigned_put_url')
    def test_nonexistent_client_raises_error(self, mock_presign):
        with self.assertRaises(ObjectDoesNotExist):
            create_presigned_upload(
                install_id='nonexistent',
                content_type='image/jpeg',
            )


class TestCompleteUpload(TestCase):
    @patch('asset.services.uploads.head_object')
    def test_completes_successfully(self, mock_head):
        mock_head.return_value = S3ObjectMetadata(
            content_type='image/jpeg',
            content_length=12345,
            etag='"abc123"',
        )
        session = UploadSessionFactory(status=UploadStatus.PRESIGNED.value)
        asset = AssetFactory(upload_session=session)

        result = complete_upload(
            upload_session_id=session.id,
            asset_id=asset.id,
        )

        self.assertEqual(result.upload_session_id, session.id)
        self.assertEqual(result.asset_id, asset.id)
        self.assertIsNotNone(result.hand_id)

        session.refresh_from_db()
        self.assertEqual(session.status, UploadStatus.COMPLETED.value)

        asset.refresh_from_db()
        self.assertTrue(asset.is_active)
        self.assertEqual(asset.byte_size, 12345)

        hand = Hand.objects.get(id=result.hand_id)
        self.assertEqual(hand.client, session.client)

    @patch('asset.services.uploads.head_object')
    def test_wrong_session_state_raises_error(self, mock_head):
        session = UploadSessionFactory(status=UploadStatus.CREATED.value)
        asset = AssetFactory(upload_session=session)

        with self.assertRaises(InvalidUploadSessionStateError):
            complete_upload(
                upload_session_id=session.id,
                asset_id=asset.id,
            )

        mock_head.assert_not_called()

    @patch('asset.services.uploads.head_object')
    def test_file_not_in_s3_raises_error(self, mock_head):
        mock_head.return_value = None
        session = UploadSessionFactory(status=UploadStatus.PRESIGNED.value)
        asset = AssetFactory(upload_session=session)

        with self.assertRaises(UploadNotCompleteError):
            complete_upload(
                upload_session_id=session.id,
                asset_id=asset.id,
            )

    @patch('asset.services.uploads.head_object')
    def test_nonexistent_session_raises_error(self, mock_head):
        with self.assertRaises(ObjectDoesNotExist):
            complete_upload(
                upload_session_id=uuid.uuid4(),
                asset_id=uuid.uuid4(),
            )

    @patch('asset.services.uploads.head_object')
    def test_nonexistent_asset_raises_error(self, mock_head):
        session = UploadSessionFactory(status=UploadStatus.PRESIGNED.value)

        with self.assertRaises(ObjectDoesNotExist):
            complete_upload(
                upload_session_id=session.id,
                asset_id=uuid.uuid4(),
            )
