import uuid
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from asset.constants import AssetRole
from asset.factories import AssetFactory, ClientFactory, UploadSessionFactory
from asset.models import AssetRef
from hand.constants import DetectionStatus
from hand.exceptions import UnknownTileLabelError
from hand.models import Hand, HandDetection, DetectionTile
from hand.services.inference import DetectedTile, InferenceResult
from hand.tasks import run_hand_detection


class TestRunHandDetection(TestCase):
    def setUp(self):
        self.client = ClientFactory()
        self.hand = Hand.objects.create(client=self.client, source='camera')
        session = UploadSessionFactory(client=self.client)
        self.asset = AssetFactory(upload_session=session, is_active=True)
        self.asset_ref = AssetRef.attach(
            asset=self.asset,
            owner=self.hand,
            role=AssetRole.HAND_PHOTO.value,
        )
        self.detection = HandDetection.objects.create(
            hand=self.hand,
            asset_ref=self.asset_ref,
            status=DetectionStatus.PENDING.value,
            model_name='tile_detector',
            model_version='v0.1.0',
        )

    @patch('hand.tasks.run_inference')
    def test_success_saves_tiles(self, mock_inference):
        mock_inference.return_value = InferenceResult(
            tiles=[
                DetectedTile(
                    tile_code='1B',
                    x1=10,
                    y1=20,
                    x2=100,
                    y2=120,
                    confidence=Decimal('0.95'),
                ),
                DetectedTile(
                    tile_code='RD',
                    x1=110,
                    y1=20,
                    x2=200,
                    y2=120,
                    confidence=Decimal('0.87'),
                ),
            ],
            confidence_overall=Decimal('0.91'),
        )

        run_hand_detection(str(self.detection.id))

        self.detection.refresh_from_db()
        self.assertEqual(
            self.detection.status,
            DetectionStatus.SUCCEEDED.value,
        )
        self.assertEqual(self.detection.confidence_overall, Decimal('0.91'))

        tiles = DetectionTile.objects.filter(detection=self.detection)
        self.assertEqual(tiles.count(), 2)

        tile_codes = [t.tile_code for t in tiles]
        self.assertIn('1B', tile_codes)
        self.assertIn('RD', tile_codes)

    @patch('hand.tasks.run_inference')
    def test_marks_running_before_inference(self, mock_inference):
        def check_status(*args, **kwargs):
            self.detection.refresh_from_db()
            self.assertEqual(
                self.detection.status,
                DetectionStatus.RUNNING.value,
            )
            return InferenceResult(tiles=[], confidence_overall=Decimal('0'))

        mock_inference.side_effect = check_status

        run_hand_detection(str(self.detection.id))

    @patch('hand.tasks.run_inference')
    def test_unknown_label_marks_failed(self, mock_inference):
        mock_inference.side_effect = UnknownTileLabelError(
            message='Unknown label: UNKNOWN',
        )

        run_hand_detection(str(self.detection.id))

        self.detection.refresh_from_db()
        self.assertEqual(self.detection.status, DetectionStatus.FAILED.value)
        self.assertEqual(self.detection.error_code, 'UnknownTileLabelError')
        self.assertIn('Unknown label', self.detection.error_message)

    @patch('hand.tasks.run_inference')
    def test_generic_error_marks_failed(self, mock_inference):
        mock_inference.side_effect = ValueError('Something went wrong')

        run_hand_detection(str(self.detection.id))

        self.detection.refresh_from_db()
        self.assertEqual(self.detection.status, DetectionStatus.FAILED.value)
        self.assertEqual(self.detection.error_code, 'ValueError')
        self.assertIn('Something went wrong', self.detection.error_message)

    def test_nonexistent_detection_logs_error(self):
        # Should not raise, just log
        run_hand_detection(str(uuid.uuid4()))

    @patch('hand.tasks.run_inference')
    def test_skips_already_succeeded(self, mock_inference):
        self.detection.status = DetectionStatus.SUCCEEDED.value
        self.detection.save()

        run_hand_detection(str(self.detection.id))

        mock_inference.assert_not_called()

    @patch('hand.tasks.run_inference')
    def test_skips_already_failed(self, mock_inference):
        self.detection.status = DetectionStatus.FAILED.value
        self.detection.save()

        run_hand_detection(str(self.detection.id))

        mock_inference.assert_not_called()
