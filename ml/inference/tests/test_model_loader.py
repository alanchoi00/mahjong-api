import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from django.test import TestCase, override_settings

from asset.services.s3 import download_file
from asset.exceptions import ModelDownloadError
from ml.inference.model_loader import (
    ensure_model_local,
    get_model_local_path,
    parse_s3_uri,
)


class TestParseS3Uri(TestCase):
    def test_parses_valid_s3_uri(self):
        bucket, key = parse_s3_uri('s3://my-bucket/path/to/model.pt')
        self.assertEqual(bucket, 'my-bucket')
        self.assertEqual(key, 'path/to/model.pt')

    def test_parses_uri_with_single_key(self):
        bucket, key = parse_s3_uri('s3://bucket/model.pt')
        self.assertEqual(bucket, 'bucket')
        self.assertEqual(key, 'model.pt')

    def test_parses_uri_with_deep_path(self):
        bucket, key = parse_s3_uri('s3://bucket/a/b/c/d/model.pt')
        self.assertEqual(bucket, 'bucket')
        self.assertEqual(key, 'a/b/c/d/model.pt')

    def test_raises_on_empty_uri(self):
        with self.assertRaises(ValueError) as ctx:
            parse_s3_uri('')
        self.assertIn('cannot be empty', str(ctx.exception))

    def test_raises_on_none_uri(self):
        with self.assertRaises(ValueError) as ctx:
            parse_s3_uri(None)
        self.assertIn('cannot be empty', str(ctx.exception))

    def test_raises_on_invalid_scheme(self):
        with self.assertRaises(ValueError) as ctx:
            parse_s3_uri('https://bucket/key')
        self.assertIn("Invalid S3 URI scheme: 'https'", str(ctx.exception))

    def test_raises_on_missing_bucket(self):
        with self.assertRaises(ValueError) as ctx:
            parse_s3_uri('s3:///key')
        self.assertIn('must include a bucket name', str(ctx.exception))

    def test_raises_on_missing_key(self):
        with self.assertRaises(ValueError) as ctx:
            parse_s3_uri('s3://bucket/')
        self.assertIn('must include an object key', str(ctx.exception))

    def test_raises_on_bucket_only(self):
        with self.assertRaises(ValueError) as ctx:
            parse_s3_uri('s3://bucket')
        self.assertIn('must include an object key', str(ctx.exception))


class TestGetModelLocalPath(TestCase):
    @override_settings(
        MODEL_DIR='/models',
        TILE_DETECTOR_MODEL_NAME='tile',
        TILE_DETECTOR_MODEL_VERSION='v1',
    )
    def test_derives_path_from_settings(self):
        result = get_model_local_path()
        self.assertEqual(result, '/models/tile/v1/model.pt')


class TestEnsureModelLocal(TestCase):
    @patch('ml.inference.model_loader.get_model_local_path')
    @patch('ml.inference.model_loader.download_file')
    @override_settings(MODEL_S3_URI='s3://b/k')
    def test_skips_download_when_file_exists(
        self,
        mock_download,
        mock_get_path,
    ):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'fake model content')
            temp_path = f.name

        try:
            mock_get_path.return_value = temp_path
            result = ensure_model_local()

            self.assertEqual(result, temp_path)
            mock_download.assert_not_called()
        finally:
            os.unlink(temp_path)

    @patch('ml.inference.model_loader.get_model_local_path')
    @patch('ml.inference.model_loader.download_file')
    @override_settings(MODEL_S3_URI='s3://bucket/path/model.pt')
    def test_downloads_when_file_missing(self, mock_download, mock_get_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, 'subdir', 'model.pt')
            mock_get_path.return_value = local_path

            def fake_download(bucket, key, path):
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                Path(path).write_bytes(b'model data')
                return 10

            mock_download.side_effect = fake_download
            result = ensure_model_local()

            self.assertEqual(result, local_path)
            mock_download.assert_called_once_with(
                'bucket',
                'path/model.pt',
                local_path,
            )
            self.assertTrue(Path(local_path).exists())

    @override_settings(MODEL_S3_URI=None)
    def test_raises_when_s3_uri_missing(self):
        with self.assertRaises(ModelDownloadError) as ctx:
            ensure_model_local()
        self.assertIn('MODEL_S3_URI', ctx.exception.message)

    @patch('ml.inference.model_loader.get_model_local_path')
    @patch('ml.inference.model_loader.download_file')
    @override_settings(MODEL_S3_URI='s3://b/k')
    def test_raises_on_download_failure(self, mock_download, mock_get_path):
        mock_download.side_effect = ModelDownloadError(message='Access Denied')

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, 'model.pt')
            mock_get_path.return_value = local_path

            with self.assertRaises(ModelDownloadError):
                ensure_model_local()

    @patch('ml.inference.model_loader.get_model_local_path')
    @patch('ml.inference.model_loader.download_file')
    @override_settings(MODEL_S3_URI='s3://b/k')
    def test_raises_on_empty_download(self, mock_download, mock_get_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, 'model.pt')
            mock_get_path.return_value = local_path

            def fake_download(bucket, key, path):
                Path(path).write_bytes(b'')
                return 0

            mock_download.side_effect = fake_download

            with self.assertRaises(ModelDownloadError) as ctx:
                ensure_model_local()
            self.assertIn('empty', ctx.exception.message)


class TestDownloadFileS3(TestCase):
    """Tests for the S3 download_file function in asset/services/s3.py."""

    @patch('asset.services.s3.get_s3_client')
    def test_downloads_file_successfully(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, 'model.pt')

            def fake_download(bucket, key, path):
                Path(path).write_bytes(b'model content here')

            mock_client.download_file.side_effect = fake_download

            size = download_file('bucket', 'key/model.pt', local_path)

            self.assertEqual(size, 18)
            mock_client.download_file.assert_called_once_with(
                'bucket',
                'key/model.pt',
                local_path,
            )

    @patch('asset.services.s3.get_s3_client')
    def test_raises_on_access_denied(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.download_file.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            'GetObject',
        )
        mock_get_client.return_value = mock_client

        with self.assertRaises(ModelDownloadError) as ctx:
            download_file('bucket', 'key', '/tmp/model.pt')
        self.assertIn('AccessDenied', ctx.exception.message)

    @patch('asset.services.s3.get_s3_client')
    def test_raises_on_not_found(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.download_file.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not Found'}},
            'GetObject',
        )
        mock_get_client.return_value = mock_client

        with self.assertRaises(ModelDownloadError) as ctx:
            download_file('bucket', 'key', '/tmp/model.pt')
        self.assertIn('404', ctx.exception.message)
