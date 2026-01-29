from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from .serializers import RegisterSerializer, LoginSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user.
    
    POST /api/auth/register/
    {
        "username": "johndoe",
        "email": "john@example.com",
        "password": "securepassword123"
    }
    """
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        # Create auth token for the user
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    
    # Format error messages for frontend
    errors = []
    for field, messages in serializer.errors.items():
        for msg in messages:
            errors.append(f"{field}: {msg}")
    
    return Response({
        'error': '; '.join(errors) if errors else 'Registration failed'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return token.
    
    POST /api/auth/login/
    {
        "username": "johndoe",
        "password": "securepassword123"
    }
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
                'token': token.key
            })
        
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'error': 'Login failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout(request):
    """
    Logout user by deleting their token.
    
    POST /api/auth/logout/
    (Requires authentication)
    """
    if request.user.is_authenticated:
        Token.objects.filter(user=request.user).delete()
        return Response({'message': 'Logged out successfully'})
    
    return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
