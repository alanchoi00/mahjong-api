from celery import shared_task

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def run_hand_detection(self, hand_id: str):
    # TODO:
    # 1) load image asset
    # 2) run YOLO
    # 3) save HandDetection + DetectionTile
    return {"hand_id": hand_id, "status": "ok"}