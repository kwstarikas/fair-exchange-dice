import logging
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models as db_models
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Game, OnlineStatus
from .serializers import GameSerializer, OnlineUserSerializer

logger = logging.getLogger(__name__)

ONLINE_THRESHOLD_SECONDS = 30


class GameViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GameSerializer

    def get_queryset(self):
        user = self.request.user
        return Game.objects.filter(
            db_models.Q(challenger=user) | db_models.Q(opponent=user)
        ).exclude(state=Game.STATE_DECLINED).order_by('-updated_at')

    # ── Heartbeat & discovery ──────────────────────────────────────────────

    @action(detail=False, methods=['post'])
    def heartbeat(self, request):
        OnlineStatus.objects.update_or_create(user=request.user, defaults={})
        return Response({'status': 'ok'})

    @action(detail=False, methods=['get'], url_path='online-users')
    def online_users(self, request):
        cutoff = timezone.now() - timedelta(seconds=ONLINE_THRESHOLD_SECONDS)
        statuses = (
            OnlineStatus.objects
            .filter(last_seen__gte=cutoff)
            .exclude(user=request.user)
            .select_related('user')
        )
        users = [s.user for s in statuses]
        return Response(OnlineUserSerializer(users, many=True).data)

    # ── Game CRUD ──────────────────────────────────────────────────────────

    def list(self, request):
        return Response(GameSerializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, pk=None):
        try:
            game = self.get_queryset().get(pk=pk)
        except Game.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(GameSerializer(game).data)

    def create(self, request):
        opponent_id = request.data.get('opponent_id')
        if not opponent_id:
            return Response({'error': 'opponent_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            opponent = User.objects.get(id=opponent_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if opponent == request.user:
            return Response({'error': 'Cannot challenge yourself'}, status=status.HTTP_400_BAD_REQUEST)

        active_states = [Game.STATE_PENDING, Game.STATE_COMMITTING, Game.STATE_REVEALING]
        existing = Game.objects.filter(
            db_models.Q(challenger=request.user, opponent=opponent) |
            db_models.Q(challenger=opponent, opponent=request.user),
            state__in=active_states,
        ).first()

        if existing:
            return Response(
                {'error': 'An active game already exists with this player'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        game = Game.objects.create(challenger=request.user, opponent=opponent)
        return Response(GameSerializer(game).data, status=status.HTTP_201_CREATED)

    # ── Challenge response ─────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        game = self._get_game_or_404(pk)
        if game is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if game.opponent != request.user:
            return Response({'error': 'Only the opponent can accept'}, status=status.HTTP_403_FORBIDDEN)
        if game.state != Game.STATE_PENDING:
            return Response({'error': 'Game is not pending'}, status=status.HTTP_400_BAD_REQUEST)

        game.state = Game.STATE_COMMITTING
        game.save()
        return Response(GameSerializer(game).data)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        game = self._get_game_or_404(pk)
        if game is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if game.opponent != request.user:
            return Response({'error': 'Only the opponent can decline'}, status=status.HTTP_403_FORBIDDEN)
        if game.state != Game.STATE_PENDING:
            return Response({'error': 'Game is not pending'}, status=status.HTTP_400_BAD_REQUEST)

        game.state = Game.STATE_DECLINED
        game.save()
        return Response({'message': 'Challenge declined'})

    # ── Bit commitment protocol ────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def commit(self, request, pk=None):
        game = self._get_game_or_404(pk)
        if game is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if game.state != Game.STATE_COMMITTING:
            return Response({'error': 'Game is not in committing phase'}, status=status.HTTP_400_BAD_REQUEST)

        commitment = request.data.get('commitment', '')
        if not commitment or len(commitment) != 64:
            return Response({'error': 'commitment must be a 64-character hex string'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user == game.challenger:
            if game.challenger_commit:
                return Response({'error': 'Already committed'}, status=status.HTTP_400_BAD_REQUEST)
            game.challenger_commit = commitment
        elif request.user == game.opponent:
            if game.opponent_commit:
                return Response({'error': 'Already committed'}, status=status.HTTP_400_BAD_REQUEST)
            game.opponent_commit = commitment
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if game.challenger_commit and game.opponent_commit:
            game.state = Game.STATE_REVEALING

        game.save()
        return Response(GameSerializer(game).data)

    @action(detail=True, methods=['post'])
    def reveal(self, request, pk=None):
        game = self._get_game_or_404(pk)
        if game is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if game.state != Game.STATE_REVEALING:
            return Response({'error': 'Game is not in revealing phase'}, status=status.HTTP_400_BAD_REQUEST)

        nonce = request.data.get('nonce', '')
        try:
            value = int(request.data.get('value'))
            if not 1 <= value <= 6:
                raise ValueError
        except (TypeError, ValueError):
            return Response({'error': 'value must be an integer between 1 and 6'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user == game.challenger:
            if game.challenger_nonce:
                return Response({'error': 'Already revealed'}, status=status.HTTP_400_BAD_REQUEST)
            if not game.verify_commitment(nonce, value, game.challenger_commit):
                return Response({'error': 'Commitment verification failed'}, status=status.HTTP_400_BAD_REQUEST)
            game.challenger_nonce = nonce
            game.challenger_value = value
        elif request.user == game.opponent:
            if game.opponent_nonce:
                return Response({'error': 'Already revealed'}, status=status.HTTP_400_BAD_REQUEST)
            if not game.verify_commitment(nonce, value, game.opponent_commit):
                return Response({'error': 'Commitment verification failed'}, status=status.HTTP_400_BAD_REQUEST)
            game.opponent_nonce = nonce
            game.opponent_value = value
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if game.challenger_value is not None and game.opponent_value is not None:
            game.state = Game.STATE_FINISHED
            if game.challenger_value > game.opponent_value:
                game.winner = game.challenger
            elif game.opponent_value > game.challenger_value:
                game.winner = game.opponent
            else:
                game.is_draw = True

        game.save()
        return Response(GameSerializer(game).data)

    # ── Helper ─────────────────────────────────────────────────────────────

    def _get_game_or_404(self, pk):
        try:
            return self.get_queryset().get(pk=pk)
        except Game.DoesNotExist:
            return None
