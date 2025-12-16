from celery import shared_task
from django.conf import settings

from ml.inference.model import get_model


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def run_hand_detection(self, hand_id: str):
    model = get_model(  # noqa: F841
        name=settings.TILE_DETECTOR_MODEL_NAME,
        version=settings.TILE_DETECTOR_MODEL_VERSION,
    )
