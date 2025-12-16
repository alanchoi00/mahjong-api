from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from asset.constants import UploadStatus
from asset.factories import AssetFactory, ClientFactory, UploadSessionFactory
from asset.services.s3 import S3ObjectMetadata


class TestUploadsViewSetPresign(APITestCase):
    @patch('asset.services.uploads.generate_presigned_put_url')
    def test_success(self, mock_presign):
        mock_presign.return_value = 'https://s3.example.com/presigned'
        client = ClientFactory()

        response = self.client.post(
            '/asset/upload/presign/',
            {
                'install_id': client.install_id,
                'content_type': 'image/jpeg',
                'purpose': 'hand_photo',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('upload_session_id', response.data)
        self.assertIn('asset_id', response.data)
        self.assertIn('presigned_url', response.data)
        self.assertIn('storage_key', response.data)

    def test_invalid_content_type(self):
        client = ClientFactory()

        response = self.client.post(
            '/asset/upload/presign/',
            {
                'install_id': client.install_id,
                'content_type': 'application/pdf',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_install_id(self):
        response = self.client.post(
            '/asset/upload/presign/',
            {
                'content_type': 'image/jpeg',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_content_type(self):
        client = ClientFactory()

        response = self.client.post(
            '/asset/upload/presign/',
            {
                'install_id': client.install_id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestUploadsViewSetComplete(APITestCase):
    @patch('asset.services.uploads.head_object')
    def test_success(self, mock_head):
        mock_head.return_value = S3ObjectMetadata(
            content_type='image/jpeg',
            content_length=12345,
            etag='"abc123"',
        )
        session = UploadSessionFactory(status=UploadStatus.PRESIGNED.value)
        asset = AssetFactory(upload_session=session)

        response = self.client.post(
            '/asset/upload/complete/',
            {
                'upload_session_id': str(session.id),
                'asset_id': str(asset.id),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('upload_session_id', response.data)
        self.assertIn('asset_id', response.data)
        self.assertIn('hand_id', response.data)
        self.assertIn('asset_ref_id', response.data)

    @patch('asset.services.uploads.head_object')
    def test_file_not_uploaded(self, mock_head):
        mock_head.return_value = None
        session = UploadSessionFactory(status=UploadStatus.PRESIGNED.value)
        asset = AssetFactory(upload_session=session)

        response = self.client.post(
            '/asset/upload/complete/',
            {
                'upload_session_id': str(session.id),
                'asset_id': str(asset.id),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'upload_not_complete')

    def test_missing_fields(self):
        response = self.client.post('/asset/upload/complete/', {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_uuid_format(self):
        response = self.client.post(
            '/asset/upload/complete/',
            {
                'upload_session_id': 'not-a-uuid',
                'asset_id': 'not-a-uuid',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
