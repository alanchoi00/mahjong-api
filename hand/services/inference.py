import tempfile
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from django.conf import settings

from asset.services.s3 import download_file
from hand.exceptions import UnknownTileLabelError
from hand.tiles import label_to_tile
from ml.inference.model import get_model


@dataclass(frozen=True)
class DetectedTile:
    tile_code: str
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: Decimal


@dataclass(frozen=True)
class InferenceResult:
    tiles: list[DetectedTile]
    confidence_overall: Decimal


def run_inference(
    storage_key: str,
    model_name: str,
    model_version: str,
) -> InferenceResult:
    """
    Run tile detection inference on an image.

    Args:
        storage_key: S3 key of the image to process.
        model_name: Name of the model to use.
        model_version: Version of the model to use.

    Returns:
        InferenceResult with detected tiles and overall confidence.

    Raises:
        UnknownTileLabelError: If model predicts an unknown label.
    """
    # Download image to temp file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        temp_path = f.name

    try:
        download_file(
            bucket_name=settings.AWS_STORAGE_BUCKET_NAME,
            object_key=storage_key,
            local_path=temp_path,
        )

        # Load model and run inference
        model = get_model(name=model_name, version=model_version)
        results = model(temp_path)

        # Process results
        tiles = []
        confidences = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for i in range(len(boxes)):
                # Get class label from model
                cls_id = int(boxes.cls[i].item())
                label = model.names[cls_id]

                # Map label to tile code
                tile = label_to_tile(label)
                if tile is None:
                    raise UnknownTileLabelError(
                        message=f'Unknown tile label from model: {label}',
                    )

                # Get bounding box
                xyxy = boxes.xyxy[i].tolist()
                conf = float(boxes.conf[i].item())

                tiles.append(
                    DetectedTile(
                        tile_code=tile.value,
                        x1=int(xyxy[0]),
                        y1=int(xyxy[1]),
                        x2=int(xyxy[2]),
                        y2=int(xyxy[3]),
                        confidence=Decimal(str(round(conf, 4))),
                    ),
                )
                confidences.append(conf)

        # Calculate overall confidence (average)
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            confidence_overall = Decimal(str(round(avg_conf, 4)))
        else:
            confidence_overall = Decimal('0')

        return InferenceResult(
            tiles=tiles,
            confidence_overall=confidence_overall,
        )

    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)
