from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


# Unregister the default User admin and re-register with customizations
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User admin with additional info."""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    """Admin for authentication tokens."""
    
    list_display = ('key', 'user', 'created')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('key', 'created')
    ordering = ('-created',)
