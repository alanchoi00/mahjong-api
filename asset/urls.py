from rest_framework.routers import DefaultRouter

from asset.views import AssetViewSet, UploadsViewSet

router = DefaultRouter()
router.register('upload', UploadsViewSet, basename='upload')
router.register('', AssetViewSet, basename='asset')

urlpatterns = router.urls
