from django.db import models


class AuditLog(models.Model):
    REGISTER = 'REGISTER'
    LOGIN_SUCCESS = 'LOGIN_SUCCESS'
    LOGIN_FAILED = 'LOGIN_FAILED'
    LOGOUT = 'LOGOUT'
    ACCOUNT_DELETE = 'ACCOUNT_DELETE'
    DATA_EXPORT = 'DATA_EXPORT'
    ADMIN_ACCESS = 'ADMIN_ACCESS'

    EVENT_CHOICES = [
        (REGISTER, 'Registration'),
        (LOGIN_SUCCESS, 'Login Success'),
        (LOGIN_FAILED, 'Login Failed'),
        (LOGOUT, 'Logout'),
        (ACCOUNT_DELETE, 'Account Deletion'),
        (DATA_EXPORT, 'Data Export'),
        (ADMIN_ACCESS, 'Admin Access'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES, db_index=True)
    # Stored as plain int, not a FK — avoids cascading deletes wiping audit trail
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event_type} user_id={self.user_id} {self.timestamp}"


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_event(event_type, request=None, user_id=None):
    ip = get_client_ip(request) if request else None
    AuditLog.objects.create(
        event_type=event_type,
        user_id=user_id,
        ip_address=ip,
    )
