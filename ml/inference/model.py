from dataclasses import dataclass
from pathlib import Path
from ultralytics import YOLO
from mahjong_api import env
import yaml

_model: YOLO | None = None


@dataclass(frozen=True)
class ModelMetadata:
    name: str
    version: str
    description: str
    input_size: int
    classes: list[str]


def get_model(name: str, version: str) -> YOLO:
    global _model
    if _model is None:
        path = Path(env.MODEL_DIR) / name / version / 'model.pt'
        _model = YOLO(path)
    return _model


def get_model_metadata(name: str, version: str) -> ModelMetadata:
    path = Path(env.MODEL_DIR) / name / version / 'metadata.yaml'
    with open(path) as f:
        metadata = yaml.safe_load(f)
    return ModelMetadata(**metadata)


def get_model_classes(name: str, version: str) -> list[str]:
    path = Path(env.MODEL_DIR) / name / version / 'labels.yaml'
    with open(path) as f:
        labels = yaml.safe_load(f)
    return getattr(labels, 'names', [])
