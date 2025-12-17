from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from django.conf import settings

# NOTE: Do NOT import ultralytics at module level!
# ultralytics imports cv2, which requires libGL.so.1 (not available in web container).
# Import lazily inside get_model() to ensure only Celery workers load it.

if TYPE_CHECKING:
    from ultralytics import YOLO

_model: 'YOLO | None' = None


@dataclass(frozen=True)
class ModelMetadata:
    name: str
    version: str
    description: str
    input_size: int
    classes: list[str]


def get_model(name: str, version: str) -> 'YOLO':
    """
    Load the YOLO model lazily.

    The ultralytics import is deferred to runtime to avoid loading cv2
    (which requires libGL.so.1) during Django startup or migrations.
    """
    global _model
    if _model is None:
        # Lazy import to avoid loading cv2 at module import time
        from ultralytics import YOLO

        path = Path(settings.MODEL_DIR) / name / version / 'model.pt'
        _model = YOLO(path)
    return _model


def get_model_metadata(name: str, version: str) -> ModelMetadata:
    path = Path(settings.MODEL_DIR) / name / version / 'metadata.yaml'
    with open(path) as f:
        metadata = yaml.safe_load(f)
    return ModelMetadata(**metadata)


def get_model_classes(name: str, version: str) -> list[str]:
    path = Path(settings.MODEL_DIR) / name / version / 'labels.yaml'
    with open(path) as f:
        labels = yaml.safe_load(f)
    return getattr(labels, 'names', [])
