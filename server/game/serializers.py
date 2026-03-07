from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Game


class OnlineUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class GameSerializer(serializers.ModelSerializer):
    challenger_username = serializers.CharField(source='challenger.username', read_only=True)
    opponent_username = serializers.CharField(source='opponent.username', read_only=True)
    winner_username = serializers.SerializerMethodField()

    def get_winner_username(self, obj):
        return obj.winner.username if obj.winner else None

    class Meta:
        model = Game
        fields = [
            'id', 'state',
            'challenger', 'challenger_username',
            'opponent', 'opponent_username',
            'challenger_commit', 'opponent_commit',
            'challenger_value', 'opponent_value',
            'winner', 'winner_username', 'is_draw',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields
