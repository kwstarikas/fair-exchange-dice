from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets
router = DefaultRouter()

# Register AuthViewSet - handles register, login, logout, me
# basename='auth' creates URLs like: auth-register, auth-login, etc.
router.register(r'auth', views.AuthViewSet, basename='auth')

# Register UserViewSet - handles list and retrieve users
# No basename needed because queryset is defined
router.register(r'users', views.UserViewSet)

# The router automatically creates the URL patterns
urlpatterns = router.urls
