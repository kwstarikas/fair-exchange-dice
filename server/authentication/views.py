from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet for authentication operations.
    
    Uses mixins pattern with custom actions:
    - POST /api/auth/register/ - Create new user
    - POST /api/auth/login/ - Login and get token
    - POST /api/auth/logout/ - Logout (delete token)
    - GET /api/auth/me/ - Get current user info
    """
    
    def get_permissions(self):
        """Allow anyone to register/login, but require auth for logout/me."""
        if self.action in ['register', 'login']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """Return appropriate serializer for each action."""
        if self.action == 'register':
            return RegisterSerializer
        elif self.action == 'login':
            return LoginSerializer
        return UserSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Register a new user.
        
        POST /api/auth/register/
        {
            "username": "johndoe",
            "email": "john@example.com",
            "password": "securepassword123"
        }
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({
                'message': 'User registered successfully',
                'user': UserSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        
        # Format error messages
        errors = []
        for field, messages in serializer.errors.items():
            for msg in messages:
                errors.append(f"{field}: {msg}")
        
        return Response({
            'error': '; '.join(errors) if errors else 'Registration failed'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Login and return token.
        
        POST /api/auth/login/
        {
            "username": "johndoe",
            "password": "securepassword123"
        }
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data,
                    'token': token.key
                })
            
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'error': 'Login failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Logout by deleting the auth token.
        
        POST /api/auth/logout/
        (Requires authentication)
        """
        Token.objects.filter(user=request.user).delete()
        return Response({'message': 'Logged out successfully'})

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current authenticated user info.
        
        GET /api/auth/me/
        (Requires authentication)
        """
        return Response(UserSerializer(request.user).data)


class UserViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    """
    ViewSet for viewing users (read-only).
    
    Uses mixins:
    - ListModelMixin: GET /api/users/ - List all users
    - RetrieveModelMixin: GET /api/users/{id}/ - Get single user
    
    This demonstrates how mixins work - you pick only
    the actions you need instead of getting all CRUD operations.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
