from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user_id', 'ip_address', 'timestamp')
    list_filter = ('event_type',)
    search_fields = ('user_id', 'ip_address')
    readonly_fields = ('event_type', 'user_id', 'ip_address', 'timestamp')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
