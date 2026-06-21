from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Avg, Exists, OuterRef
from django.utils import timezone

from .models import User, Avis
from .forms import InscriptionVendeurForm, ConnexionForm, ProfilForm
from listings.models import Annonce, Boost, Favori


def inscription(request):
    if request.user.is_authenticated:
        return redirect('accounts:tableau_de_bord')
    if request.method == 'POST':
        form = InscriptionVendeurForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenue {user.first_name} ! Votre compte vendeur a été créé.')
            return redirect('accounts:tableau_de_bord')
    else:
        form = InscriptionVendeurForm()
    return render(request, 'accounts/inscription.html', {'form': form})


def connexion(request):
    if request.user.is_authenticated:
        return redirect('accounts:tableau_de_bord')
    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bon retour, {user.first_name} !')
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('accounts:tableau_de_bord')
    else:
        form = ConnexionForm()
    return render(request, 'accounts/connexion.html', {'form': form})


@require_http_methods(['POST'])
def deconnexion(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('home')


@login_required
def tableau_de_bord(request):
    boost_qs = Boost.objects.filter(
        annonce=OuterRef('pk'), statut='actif', date_fin__gt=timezone.now()
    )
    annonces = (
        Annonce.objects.filter(vendeur=request.user)
        .annotate(est_booste=Exists(boost_qs))
        .order_by('-date_creation')
    )
    stats = {
        'total': annonces.count(),
        'actives': annonces.filter(statut='active').count(),
        'en_attente': annonces.filter(statut='en_attente').count(),
    }
    return render(request, 'accounts/tableau_de_bord.html', {
        'annonces': annonces,
        'stats': stats,
    })


@login_required
def profil(request):
    if request.method == 'POST':
        form = ProfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.save(update_fields=['first_name', 'last_name', 'telephone', 'ville', 'bio', 'photo_profil'])
            messages.success(request, 'Votre profil a été mis à jour.')
            return redirect('accounts:profil')
    else:
        form = ProfilForm(instance=request.user)
    return render(request, 'accounts/profil.html', {'form': form})


def profil_vendeur(request, pk):
    from messaging.models import Conversation

    vendeur = get_object_or_404(User, pk=pk)

    boost_qs = Boost.objects.filter(
        annonce=OuterRef('pk'), statut='actif', date_fin__gt=timezone.now()
    )
    annonces_qs = (
        Annonce.objects.filter(vendeur=vendeur, statut='active')
        .annotate(est_booste=Exists(boost_qs))
        .prefetch_related('photos')
        .order_by('-est_booste', '-date_creation')
    )
    nb_annonces = annonces_qs.count()
    annonces = list(annonces_qs[:6])

    avis_qs = Avis.objects.filter(vendeur=vendeur).select_related('auteur')
    note_moyenne = avis_qs.aggregate(avg=Avg('note'))['avg']
    if note_moyenne is not None:
        note_moyenne = round(note_moyenne, 1)

    peut_laisser_avis = False
    a_deja_un_avis = False
    mon_avis = None
    if request.user.is_authenticated and request.user != vendeur:
        peut_laisser_avis = Conversation.objects.filter(
            acheteur=request.user, vendeur=vendeur
        ).exists()
        try:
            mon_avis = Avis.objects.get(auteur=request.user, vendeur=vendeur)
            a_deja_un_avis = True
        except Avis.DoesNotExist:
            pass

    favoris_ids = set()
    if request.user.is_authenticated:
        ids = [a.pk for a in annonces]
        if ids:
            favoris_ids = set(
                Favori.objects.filter(utilisateur=request.user, annonce_id__in=ids)
                .values_list('annonce_id', flat=True)
            )

    nb_avis = avis_qs.count()
    return render(request, 'accounts/profil_vendeur.html', {
        'vendeur': vendeur,
        'annonces': annonces,
        'nb_annonces': nb_annonces,
        'avis': avis_qs,
        'note_moyenne': note_moyenne,
        'nb_avis': nb_avis,
        'peut_laisser_avis': peut_laisser_avis,
        'a_deja_un_avis': a_deja_un_avis,
        'mon_avis': mon_avis,
        'favoris_ids': favoris_ids,
    })


@login_required
def analytics_vendeur(request):
    import json
    from datetime import date, timedelta
    from django.db.models import Count
    from messaging.models import Message

    today = date.today()
    debut_14j = today - timedelta(days=13)
    debut_7j = today - timedelta(days=6)

    annonces = list(
        Annonce.objects.filter(vendeur=request.user)
        .prefetch_related('photos')
        .order_by('-date_creation')
    )
    annonce_ids = [a.pk for a in annonces]

    # Vues chart — 14 jours glissants
    from listings.models import VueAnnonce
    vues_by_day = (
        VueAnnonce.objects
        .filter(annonce_id__in=annonce_ids, date__gte=debut_14j)
        .values('date')
        .annotate(count=Count('id'))
    )
    vues_map = {v['date']: v['count'] for v in vues_by_day}
    jours = [debut_14j + timedelta(days=i) for i in range(14)]
    chart_labels = json.dumps([j.strftime('%d/%m') for j in jours])
    chart_data = json.dumps([vues_map.get(j, 0) for j in jours])

    # Favoris par annonce
    favoris_counts = {
        f['annonce_id']: f['count']
        for f in Favori.objects.filter(annonce_id__in=annonce_ids)
        .values('annonce_id').annotate(count=Count('id'))
    }
    # Messages reçus (non envoyés par le vendeur) par annonce
    messages_counts = {
        m['conversation__annonce_id']: m['count']
        for m in Message.objects.filter(
            conversation__annonce_id__in=annonce_ids,
            conversation__vendeur=request.user,
        ).exclude(expediteur=request.user)
        .values('conversation__annonce_id').annotate(count=Count('id'))
    }
    # Vues 7 jours par annonce
    vues_7j_counts = {
        v['annonce_id']: v['count']
        for v in VueAnnonce.objects.filter(
            annonce_id__in=annonce_ids, date__gte=debut_7j
        ).values('annonce_id').annotate(count=Count('id'))
    }

    annonce_stats = sorted([
        {
            'annonce': a,
            'vues_7j': vues_7j_counts.get(a.pk, 0),
            'total_vues': a.vues,
            'messages': messages_counts.get(a.pk, 0),
            'favoris': favoris_counts.get(a.pk, 0),
        }
        for a in annonces
    ], key=lambda x: x['vues_7j'], reverse=True)

    totaux = {
        'vues_7j': sum(s['vues_7j'] for s in annonce_stats),
        'total_vues': sum(s['total_vues'] for s in annonce_stats),
        'messages': sum(s['messages'] for s in annonce_stats),
        'favoris': sum(s['favoris'] for s in annonce_stats),
    }

    return render(request, 'accounts/analytics.html', {
        'annonce_stats': annonce_stats,
        'totaux': totaux,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    })


@login_required
@require_POST
def laisser_avis(request, vendeur_pk):
    from messaging.models import Conversation

    vendeur = get_object_or_404(User, pk=vendeur_pk)

    if request.user == vendeur:
        messages.error(request, "Vous ne pouvez pas vous noter vous-même.")
        return redirect('accounts:profil_vendeur', pk=vendeur_pk)

    if not Conversation.objects.filter(acheteur=request.user, vendeur=vendeur).exists():
        messages.error(request, "Vous devez avoir été en contact avec ce vendeur pour laisser un avis.")
        return redirect('accounts:profil_vendeur', pk=vendeur_pk)

    try:
        note = int(request.POST.get('note', 0))
        if not (1 <= note <= 5):
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, "Note invalide. Choisissez entre 1 et 5 étoiles.")
        return redirect('accounts:profil_vendeur', pk=vendeur_pk)

    commentaire = request.POST.get('commentaire', '').strip()[:1000]

    Avis.objects.update_or_create(
        auteur=request.user,
        vendeur=vendeur,
        defaults={'note': note, 'commentaire': commentaire},
    )
    messages.success(request, "Votre avis a bien été enregistré. Merci !")
    return redirect('accounts:profil_vendeur', pk=vendeur_pk)
