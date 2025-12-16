import os

from celery import Celery
from celery.signals import worker_init

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mahjong_api.settings')

app = Celery('mahjong_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@worker_init.connect
def on_worker_init(**kwargs):
    """
    Download model weights from S3 on Celery worker startup.

    This runs once per worker process before it starts consuming tasks.
    If download fails, the worker exits with code 1 so ECS can restart it.
    """
    from ml.inference.model_loader import load_model_on_worker_startup

    load_model_on_worker_startup()
