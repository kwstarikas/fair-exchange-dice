from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from .views import CookieTokenRefreshView

router = DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('auth/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
] + router.urls
