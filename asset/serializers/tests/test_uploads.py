import uuid

from django.test import TestCase

from asset.serializers.uploads import (
    CompleteResponseSerializer,
    PresignRequestSerializer,
    PresignResponseSerializer,
)


class TestPresignRequestSerializer(TestCase):
    def test_valid_data(self):
        data = {
            'content_type': 'image/jpeg',
            'purpose': 'hand_photo',
        }
        serializer = PresignRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data['content_type'],
            'image/jpeg',
        )

    def test_valid_without_purpose(self):
        data = {
            'content_type': 'image/png',
        }
        serializer = PresignRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_invalid_missing_content_type(self):
        data = {}
        serializer = PresignRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('content_type', serializer.errors)

    def test_invalid_content_type_not_in_choices(self):
        data = {
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
            'storage_key': 'uploads/client123/hand_photo/asset.jpg',
        }
        serializer = PresignResponseSerializer(instance=data)

        self.assertIn('upload_session_id', serializer.data)
        self.assertIn('asset_id', serializer.data)
        self.assertEqual(
            serializer.data['presigned_url'],
            data['presigned_url'],
        )
        self.assertEqual(serializer.data['storage_key'], data['storage_key'])


class TestCompleteResponseSerializer(TestCase):
    def test_serializes_data(self):
        data = {
            'upload_session_id': uuid.uuid4(),
            'asset_id': uuid.uuid4(),
            'is_active': True,
            'byte_size': 12345,
            'checksum': '"abc123"',
        }
        serializer = CompleteResponseSerializer(instance=data)

        self.assertIn('upload_session_id', serializer.data)
        self.assertIn('asset_id', serializer.data)
        self.assertIn('is_active', serializer.data)
        self.assertIn('byte_size', serializer.data)
        self.assertIn('checksum', serializer.data)
        self.assertTrue(serializer.data['is_active'])
        self.assertEqual(serializer.data['byte_size'], 12345)
