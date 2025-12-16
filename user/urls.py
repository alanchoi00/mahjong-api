from rest_framework.routers import DefaultRouter

from user.views import ClientsViewSet

router = DefaultRouter()
router.register('client', ClientsViewSet, basename='client')

urlpatterns = router.urls
