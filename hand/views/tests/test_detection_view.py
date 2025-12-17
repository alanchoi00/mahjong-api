import uuid
from unittest.mock import patch

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from asset.constants import AssetRole, UploadStatus
from asset.factories import AssetFactory, ClientFactory, UploadSessionFactory
from asset.models import AssetRef
from hand.constants import DetectionStatus
from hand.models import Hand, HandDetection


@override_settings(
    TILE_DETECTOR_MODEL_NAME='tile_detector',
    TILE_DETECTOR_MODEL_VERSION='v0.1.0',
)
class TestDetectionViewSetTrigger(APITestCase):
    @patch('hand.services.detection.current_app.send_task')
    def test_success(self, mock_send_task):
        session = UploadSessionFactory(status=UploadStatus.COMPLETED.value)
        asset = AssetFactory(upload_session=session, is_active=True)

        response = self.client.post(
            '/hand/detect/',
            {'asset_id': str(asset.id), 'source': 'camera'},
            HTTP_X_INSTALL_ID=session.client.install_id,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('hand_id', response.data)
        self.assertIn('asset_ref_id', response.data)
        self.assertIn('hand_detection_id', response.data)
        self.assertEqual(
            response.data['status'],
            DetectionStatus.PENDING.value,
        )

        mock_send_task.assert_called_once()

    @patch('hand.services.detection.current_app.send_task')
    def test_default_source(self, mock_send_task):
        session = UploadSessionFactory(status=UploadStatus.COMPLETED.value)
        asset = AssetFactory(upload_session=session, is_active=True)

        response = self.client.post(
            '/hand/detect/',
            {'asset_id': str(asset.id)},
            HTTP_X_INSTALL_ID=session.client.install_id,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_missing_install_id_header(self):
        response = self.client.post(
            '/hand/detect/',
            {'asset_id': str(uuid.uuid4())},
        )

        # NotAuthenticated returns 403 in DRF when no auth classes configured
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_asset_id(self):
        client = ClientFactory()

        response = self.client.post(
            '/hand/detect/',
            {},
            HTTP_X_INSTALL_ID=client.install_id,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('hand.services.detection.current_app.send_task')
    def test_asset_not_active(self, mock_send_task):
        session = UploadSessionFactory(status=UploadStatus.PRESIGNED.value)
        asset = AssetFactory(upload_session=session, is_active=False)

        response = self.client.post(
            '/hand/detect/',
            {'asset_id': str(asset.id)},
            HTTP_X_INSTALL_ID=session.client.install_id,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'asset_not_active')

        mock_send_task.assert_not_called()

    @patch('hand.services.detection.current_app.send_task')
    def test_ownership_validation(self, mock_send_task):
        session = UploadSessionFactory(status=UploadStatus.COMPLETED.value)
        asset = AssetFactory(upload_session=session, is_active=True)
        other_client = ClientFactory()

        response = self.client.post(
            '/hand/detect/',
            {'asset_id': str(asset.id)},
            HTTP_X_INSTALL_ID=other_client.install_id,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['code'], 'asset_ownership_error')

        mock_send_task.assert_not_called()


class TestDetectionViewSetRetrieve(APITestCase):
    def test_success_pending(self):
        client = ClientFactory()
        hand = Hand.objects.create(client=client, source='camera')
        session = UploadSessionFactory(client=client)
        asset = AssetFactory(upload_session=session, is_active=True)
        asset_ref = AssetRef.attach(
            asset=asset,
            owner=hand,
            role=AssetRole.HAND_PHOTO.value,
        )
        detection = HandDetection.objects.create(
            hand=hand,
            asset_ref=asset_ref,
            status=DetectionStatus.PENDING.value,
            model_name='tile_detector',
            model_version='v0.1.0',
        )

        response = self.client.get(
            f'/hand/detect/{detection.id}/',
            HTTP_X_INSTALL_ID=client.install_id,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['hand_detection_id'],
            str(detection.id),
        )
        self.assertEqual(
            response.data['status'],
            DetectionStatus.PENDING.value,
        )
        self.assertEqual(response.data['tiles'], [])

    def test_missing_install_id_header(self):
        response = self.client.get(f'/hand/detect/{uuid.uuid4()}/')

        # NotAuthenticated returns 403 in DRF when no auth classes configured
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_found(self):
        client = ClientFactory()

        response = self.client.get(
            f'/hand/detect/{uuid.uuid4()}/',
            HTTP_X_INSTALL_ID=client.install_id,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['code'], 'detection_not_found')

    def test_ownership_validation(self):
        client = ClientFactory()
        other_client = ClientFactory()
        hand = Hand.objects.create(client=client, source='camera')
        session = UploadSessionFactory(client=client)
        asset = AssetFactory(upload_session=session, is_active=True)
        asset_ref = AssetRef.attach(
            asset=asset,
            owner=hand,
            role=AssetRole.HAND_PHOTO.value,
        )
        detection = HandDetection.objects.create(
            hand=hand,
            asset_ref=asset_ref,
            status=DetectionStatus.PENDING.value,
        )

        response = self.client.get(
            f'/hand/detect/{detection.id}/',
            HTTP_X_INSTALL_ID=other_client.install_id,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['code'], 'detection_ownership_error')
