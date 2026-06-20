from django.db.models import Q
from .models import Message


def messages_non_lus(request):
    if not request.user.is_authenticated:
        return {'messages_non_lus': 0}
    count = Message.objects.filter(
        Q(conversation__acheteur=request.user) | Q(conversation__vendeur=request.user),
        lu=False,
    ).exclude(expediteur=request.user).count()
    return {'messages_non_lus': count}
