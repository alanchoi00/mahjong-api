import uuid
from unittest.mock import patch

from django.test import TestCase, override_settings

from asset.constants import AssetRole, UploadStatus
from asset.factories import AssetFactory, ClientFactory, UploadSessionFactory
from asset.models import AssetRef
from hand.constants import DetectionStatus
from hand.exceptions import (
    AssetNotActiveError,
    AssetOwnershipError,
    DetectionNotFoundError,
    DetectionOwnershipError,
)
from hand.models import Hand, HandDetection
from hand.services.detection import (
    get_hand_detection,
    trigger_hand_detection,
)


@override_settings(
    TILE_DETECTOR_MODEL_NAME='tile_detector',
    TILE_DETECTOR_MODEL_VERSION='v0.1.0',
)
class TestTriggerHandDetection(TestCase):
    @patch('hand.services.detection.current_app.send_task')
    def test_creates_hand_asset_ref_detection(self, mock_send_task):
        session = UploadSessionFactory(status=UploadStatus.COMPLETED.value)
        asset = AssetFactory(upload_session=session, is_active=True)

        result = trigger_hand_detection(
            asset_id=asset.id,
            install_id=session.client.install_id,
            source='camera',
        )

        self.assertIsNotNone(result.hand_id)
        self.assertIsNotNone(result.asset_ref_id)
        self.assertIsNotNone(result.hand_detection_id)
        self.assertEqual(result.status, DetectionStatus.PENDING.value)

        # Verify Hand was created
        hand = Hand.objects.get(id=result.hand_id)
        self.assertEqual(hand.client, session.client)
        self.assertEqual(hand.source, 'camera')

        # Verify AssetRef was created
        asset_ref = AssetRef.objects.get(id=result.asset_ref_id)
        self.assertEqual(asset_ref.asset, asset)
        self.assertEqual(asset_ref.owner_id, hand.id)
        self.assertEqual(asset_ref.role, AssetRole.HAND_PHOTO.value)

        # Verify HandDetection was created
        detection = HandDetection.objects.get(id=result.hand_detection_id)
        self.assertEqual(detection.hand, hand)
        self.assertEqual(detection.asset_ref, asset_ref)
        self.assertEqual(detection.status, DetectionStatus.PENDING.value)
        self.assertEqual(detection.model_name, 'tile_detector')
        self.assertEqual(detection.model_version, 'v0.1.0')

        # Verify Celery task was enqueued via send_task
        mock_send_task.assert_called_once_with(
            'hand.tasks.run_hand_detection',
            args=[str(detection.id)],
        )

    @patch('hand.services.detection.current_app.send_task')
    def test_ownership_validation_fails(self, mock_send_task):
        session = UploadSessionFactory(status=UploadStatus.COMPLETED.value)
        asset = AssetFactory(upload_session=session, is_active=True)
        other_client = ClientFactory()

        with self.assertRaises(AssetOwnershipError):
            trigger_hand_detection(
                asset_id=asset.id,
                install_id=other_client.install_id,
            )

        mock_send_task.assert_not_called()

    @patch('hand.services.detection.current_app.send_task')
    def test_asset_not_active_fails(self, mock_send_task):
        session = UploadSessionFactory(status=UploadStatus.PRESIGNED.value)
        asset = AssetFactory(upload_session=session, is_active=False)

        with self.assertRaises(AssetNotActiveError):
            trigger_hand_detection(
                asset_id=asset.id,
                install_id=session.client.install_id,
            )

        mock_send_task.assert_not_called()

    @patch('hand.services.detection.current_app.send_task')
    def test_idempotency_returns_existing_pending(self, mock_send_task):
        session = UploadSessionFactory(status=UploadStatus.COMPLETED.value)
        asset = AssetFactory(upload_session=session, is_active=True)

        # First trigger
        result1 = trigger_hand_detection(
            asset_id=asset.id,
            install_id=session.client.install_id,
        )

        # Second trigger - should return existing
        result2 = trigger_hand_detection(
            asset_id=asset.id,
            install_id=session.client.install_id,
        )

        self.assertEqual(result1.hand_detection_id, result2.hand_detection_id)
        self.assertEqual(mock_send_task.call_count, 1)

    @patch('hand.services.detection.current_app.send_task')
    def test_idempotency_creates_new_on_failed(self, mock_send_task):
        session = UploadSessionFactory(status=UploadStatus.COMPLETED.value)
        asset = AssetFactory(upload_session=session, is_active=True)

        # First trigger
        result1 = trigger_hand_detection(
            asset_id=asset.id,
            install_id=session.client.install_id,
        )

        # Mark first detection as failed
        detection = HandDetection.objects.get(id=result1.hand_detection_id)
        detection.status = DetectionStatus.FAILED.value
        detection.save()

        # Second trigger - should create new
        result2 = trigger_hand_detection(
            asset_id=asset.id,
            install_id=session.client.install_id,
        )

        self.assertNotEqual(
            result1.hand_detection_id,
            result2.hand_detection_id,
        )
        self.assertEqual(mock_send_task.call_count, 2)


class TestGetHandDetection(TestCase):
    def test_returns_detection_with_tiles(self):
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
        )

        result = get_hand_detection(
            hand_detection_id=detection.id,
            install_id=client.install_id,
        )

        self.assertEqual(result.id, detection.id)
        self.assertEqual(result.status, DetectionStatus.PENDING.value)

    def test_not_found_raises_error(self):
        with self.assertRaises(DetectionNotFoundError):
            get_hand_detection(
                hand_detection_id=uuid.uuid4(),
                install_id='any',
            )

    def test_ownership_validation_fails(self):
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

        with self.assertRaises(DetectionOwnershipError):
            get_hand_detection(
                hand_detection_id=detection.id,
                install_id=other_client.install_id,
            )
