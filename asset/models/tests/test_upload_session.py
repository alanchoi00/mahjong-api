import uuid

from django.test import TestCase

from asset.constants import UploadStatus, UploadPurpose
from asset.models import UploadSession
from user.models import Client


class TestUploadSessionModel(TestCase):
    def setUp(self):
        self.client = Client.objects.create(install_id='test-client-upload')

    def test_create_upload_session_with_defaults(self):
        session = UploadSession.objects.create(client=self.client)

        self.assertIsInstance(session.id, uuid.UUID)
        self.assertEqual(session.client, self.client)
        self.assertEqual(session.status, UploadStatus.CREATED.value)
        self.assertEqual(session.purpose, '')
        self.assertIsNotNone(session.created_at)
        self.assertIsNotNone(session.updated_at)

    def test_create_upload_session_with_purpose(self):
        session = UploadSession.objects.create(
            client=self.client,
            purpose=UploadPurpose.HAND_PHOTO.value,
        )

        self.assertEqual(session.purpose, UploadPurpose.HAND_PHOTO.value)

    def test_upload_session_status_transitions(self):
        session = UploadSession.objects.create(client=self.client)
        self.assertEqual(session.status, UploadStatus.CREATED.value)

        session.status = UploadStatus.COMPLETED.value
        session.save()

        session.refresh_from_db()
        self.assertEqual(session.status, UploadStatus.COMPLETED.value)

    def test_upload_session_client_relationship(self):
        session1 = UploadSession.objects.create(client=self.client)
        session2 = UploadSession.objects.create(client=self.client)

        self.assertEqual(self.client.upload_sessions.count(), 2)
        self.assertIn(session1, self.client.upload_sessions.all())
        self.assertIn(session2, self.client.upload_sessions.all())

    def test_upload_session_cascade_delete_with_client(self):
        UploadSession.objects.create(client=self.client)
        UploadSession.objects.create(client=self.client)

        self.assertEqual(UploadSession.objects.count(), 2)

        self.client.delete()

        self.assertEqual(UploadSession.objects.count(), 0)
