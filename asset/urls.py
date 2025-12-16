from rest_framework.routers import DefaultRouter

from asset.views import UploadsViewSet

router = DefaultRouter()
router.register('upload', UploadsViewSet, basename='upload')

urlpatterns = router.urls
