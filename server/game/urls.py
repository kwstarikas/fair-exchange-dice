from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'game', views.GameViewSet, basename='game')

urlpatterns = router.urls
