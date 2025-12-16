from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError
from django.test import TestCase

from asset.exceptions import S3Error
from asset.services.s3 import (
    generate_presigned_put_url,
    head_object,
)


class TestHeadObject(TestCase):
    @patch('asset.services.s3.get_s3_client')
    def test_returns_metadata_when_exists(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.head_object.return_value = {
            'ContentType': 'image/jpeg',
            'ContentLength': 12345,
            'ETag': '"abc123"',
        }
        mock_get_client.return_value = mock_client

        result = head_object('bucket', 'key')

        self.assertIsNotNone(result)
        self.assertEqual(result.content_type, 'image/jpeg')
        self.assertEqual(result.content_length, 12345)
        self.assertEqual(result.etag, '"abc123"')

    @patch('asset.services.s3.get_s3_client')
    def test_returns_none_when_not_found(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.head_object.side_effect = ClientError(
            {'Error': {'Code': '404'}},
            'HeadObject',
        )
        mock_get_client.return_value = mock_client

        result = head_object('bucket', 'key')

        self.assertIsNone(result)

    @patch('asset.services.s3.get_s3_client')
    def test_raises_s3_error_on_other_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.head_object.side_effect = ClientError(
            {'Error': {'Code': '500'}},
            'HeadObject',
        )
        mock_get_client.return_value = mock_client

        with self.assertRaises(S3Error):
            head_object('bucket', 'key')


class TestGeneratePresignedPutUrl(TestCase):
    @patch('asset.services.s3.get_s3_client')
    def test_returns_presigned_url(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = (
            'https://presigned.url'
        )
        mock_get_client.return_value = mock_client

        result = generate_presigned_put_url('bucket', 'key', 'image/jpeg')

        self.assertEqual(result, 'https://presigned.url')
        mock_client.generate_presigned_url.assert_called_once()

    @patch('asset.services.s3.get_s3_client')
    def test_raises_s3_error_on_failure(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': '500'}},
            'GeneratePresignedUrl',
        )
        mock_get_client.return_value = mock_client

        with self.assertRaises(S3Error):
            generate_presigned_put_url('bucket', 'key', 'image/jpeg')
