import uuid

from django.test import TestCase

from asset.serializers.uploads import (
    CompleteRequestSerializer,
    CompleteResponseSerializer,
    PresignRequestSerializer,
    PresignResponseSerializer,
)


class TestPresignRequestSerializer(TestCase):
    def test_valid_data(self):
        data = {
            'install_id': 'client123',
            'content_type': 'image/jpeg',
            'purpose': 'hand_photo',
        }
        serializer = PresignRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['install_id'], 'client123')
        self.assertEqual(
            serializer.validated_data['content_type'],
            'image/jpeg',
        )

    def test_valid_without_purpose(self):
        data = {
            'install_id': 'client123',
            'content_type': 'image/png',
        }
        serializer = PresignRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_invalid_missing_install_id(self):
        data = {
            'content_type': 'image/jpeg',
        }
        serializer = PresignRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('install_id', serializer.errors)

    def test_invalid_missing_content_type(self):
        data = {
            'install_id': 'client123',
        }
        serializer = PresignRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('content_type', serializer.errors)

    def test_invalid_content_type_not_in_choices(self):
        data = {
            'install_id': 'client123',
            'content_type': 'application/pdf',
        }
        serializer = PresignRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('content_type', serializer.errors)


class TestPresignResponseSerializer(TestCase):
    def test_serializes_data(self):
        data = {
            'upload_session_id': uuid.uuid4(),
            'asset_id': uuid.uuid4(),
            'presigned_url': 'https://s3.example.com/presigned',
            'storage_key': 'uploads/client123/asset.jpg',
        }
        serializer = PresignResponseSerializer(instance=data)

        self.assertIn('upload_session_id', serializer.data)
        self.assertIn('asset_id', serializer.data)
        self.assertEqual(
            serializer.data['presigned_url'],
            data['presigned_url'],
        )
        self.assertEqual(serializer.data['storage_key'], data['storage_key'])


class TestCompleteRequestSerializer(TestCase):
    def test_valid_data(self):
        data = {
            'upload_session_id': str(uuid.uuid4()),
            'asset_id': str(uuid.uuid4()),
        }
        serializer = CompleteRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_valid_with_captured_at(self):
        data = {
            'upload_session_id': str(uuid.uuid4()),
            'asset_id': str(uuid.uuid4()),
            'captured_at': '2024-01-15T10:30:00Z',
        }
        serializer = CompleteRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_invalid_missing_upload_session_id(self):
        data = {
            'asset_id': str(uuid.uuid4()),
        }
        serializer = CompleteRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('upload_session_id', serializer.errors)

    def test_invalid_missing_asset_id(self):
        data = {
            'upload_session_id': str(uuid.uuid4()),
        }
        serializer = CompleteRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('asset_id', serializer.errors)

    def test_invalid_uuid_format(self):
        data = {
            'upload_session_id': 'not-a-uuid',
            'asset_id': 'not-a-uuid',
        }
        serializer = CompleteRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())


class TestCompleteResponseSerializer(TestCase):
    def test_serializes_data(self):
        data = {
            'upload_session_id': uuid.uuid4(),
            'asset_id': uuid.uuid4(),
            'hand_id': uuid.uuid4(),
            'asset_ref_id': uuid.uuid4(),
        }
        serializer = CompleteResponseSerializer(instance=data)

        self.assertIn('upload_session_id', serializer.data)
        self.assertIn('asset_id', serializer.data)
        self.assertIn('hand_id', serializer.data)
        self.assertIn('asset_ref_id', serializer.data)
