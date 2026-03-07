import hashlib

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class OnlineStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='online_status')
    last_seen = models.DateTimeField(auto_now=True)

    @property
    def is_online(self):
        return (timezone.now() - self.last_seen).total_seconds() < 30

    def __str__(self):
        return f"{self.user.username} ({'online' if self.is_online else 'offline'})"


class Game(models.Model):
    STATE_PENDING = 'pending'
    STATE_COMMITTING = 'committing'
    STATE_REVEALING = 'revealing'
    STATE_FINISHED = 'finished'
    STATE_DECLINED = 'declined'

    STATE_CHOICES = [
        (STATE_PENDING, 'Pending'),
        (STATE_COMMITTING, 'Committing'),
        (STATE_REVEALING, 'Revealing'),
        (STATE_FINISHED, 'Finished'),
        (STATE_DECLINED, 'Declined'),
    ]

    challenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenged_games')
    opponent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opponent_games')
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_PENDING)

    # Bit commitment fields
    challenger_commit = models.CharField(max_length=64, blank=True)
    opponent_commit = models.CharField(max_length=64, blank=True)
    challenger_nonce = models.CharField(max_length=64, blank=True)
    challenger_value = models.IntegerField(null=True, blank=True)
    opponent_nonce = models.CharField(max_length=64, blank=True)
    opponent_value = models.IntegerField(null=True, blank=True)

    winner = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='won_games'
    )
    is_draw = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def verify_commitment(self, nonce: str, value: int, commitment: str) -> bool:
        expected = hashlib.sha256(f"{nonce}{value}".encode()).hexdigest()
        return expected == commitment

    def __str__(self):
        return f"Game {self.id}: {self.challenger} vs {self.opponent} [{self.state}]"
