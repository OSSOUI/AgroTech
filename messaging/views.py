from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST

from listings.models import Annonce
from .models import Conversation, Message


@login_required
def inbox(request):
    conversations = Conversation.objects.filter(
        Q(acheteur=request.user) | Q(vendeur=request.user)
    ).select_related('annonce', 'acheteur', 'vendeur').prefetch_related('messages')

    user_id = request.user.id
    convs_data = []
    for conv in conversations:
        # Count from prefetch cache to avoid N+1 queries
        non_lus = sum(1 for m in conv.messages.all() if not m.lu and m.expediteur_id != user_id)
        convs_data.append({'conv': conv, 'non_lus': non_lus})

    return render(request, 'messaging/inbox.html', {'convs_data': convs_data})


@login_required
def conversation(request, conv_pk):
    conv = get_object_or_404(
        Conversation.objects.select_related('annonce', 'acheteur', 'vendeur'),
        pk=conv_pk
    )

    if request.user not in (conv.acheteur, conv.vendeur):
        messages.error(request, "Accès non autorisé.")
        return redirect('messaging:inbox')

    conv.messages.filter(lu=False).exclude(expediteur=request.user).update(lu=True)

    if request.method == 'POST':
        contenu = request.POST.get('contenu', '').strip()
        if contenu:
            Message.objects.create(
                conversation=conv,
                expediteur=request.user,
                contenu=contenu,
            )
            conv.save()
        return redirect('messaging:conversation', conv_pk=conv.pk)

    msgs = conv.messages.select_related('expediteur').all()
    return render(request, 'messaging/conversation.html', {
        'conv': conv,
        'msgs': msgs,
    })


@login_required
@require_POST
def demarrer_conversation(request, annonce_pk):
    annonce = get_object_or_404(Annonce, pk=annonce_pk, statut='active')

    if request.user == annonce.vendeur:
        messages.warning(request, "Vous ne pouvez pas vous envoyer un message.")
        return redirect(annonce.get_absolute_url())

    contenu = request.POST.get('contenu', '').strip()
    if not contenu:
        messages.error(request, "Le message ne peut pas être vide.")
        return redirect(annonce.get_absolute_url())

    conv, _ = Conversation.objects.get_or_create(
        annonce=annonce,
        acheteur=request.user,
        defaults={'vendeur': annonce.vendeur},
    )
    Message.objects.create(conversation=conv, expediteur=request.user, contenu=contenu)
    conv.save()

    messages.success(request, "Votre message a été envoyé au vendeur.")
    return redirect('messaging:conversation', conv_pk=conv.pk)
