import json
from urllib.parse import quote
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Exists, OuterRef
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from django.db.models import F
from .models import Annonce, AnnoncePhoto, Favori, Boost, VueAnnonce
from .forms import AnnonceForm, FiltreAnnonceForm

COORDS_REGIONS = {
    'tanger-tetouan': (35.7595, -5.8340),
    'oriental':       (34.6814, -1.9086),
    'fes-meknes':     (33.9716, -5.0078),
    'rabat-sale':     (34.0209, -6.8416),
    'beni-mellal':    (32.3372, -6.3498),
    'casablanca':     (33.5731, -7.5898),
    'marrakech':      (31.6295, -7.9811),
    'draa-tafilalet': (31.9314, -4.4244),
    'souss-massa':    (30.4278, -9.5981),
    'guelmim':        (28.9870, -10.0574),
    'laayoune':       (27.1418, -13.1875),
    'dakhla':         (23.6847, -15.9571),
}

_ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
_MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 Mo


def _valider_photos(photos):
    import os
    valides = []
    for photo in photos:
        ext = os.path.splitext(photo.name)[1].lower()
        if ext in _ALLOWED_IMAGE_EXTENSIONS and photo.size <= _MAX_IMAGE_SIZE:
            valides.append(photo)
    return valides


BOOST_PACKAGES = [
    {'duree': 7,  'prix': 199, 'label': 'Starter',  'description': 'Idéal pour tester la visibilité', 'popular': False},
    {'duree': 14, 'prix': 349, 'label': 'Pro',       'description': 'Le plus demandé par nos vendeurs', 'popular': True},
    {'duree': 30, 'prix': 599, 'label': 'Premium',   'description': 'Visibilité maximale sur un mois',  'popular': False},
]
BOOST_TARIFS = {pkg['duree']: pkg['prix'] for pkg in BOOST_PACKAGES}


def home(request):
    boost_qs = Boost.objects.filter(annonce=OuterRef('pk'), statut='actif', date_fin__gt=timezone.now())
    annonces_recentes = (
        Annonce.objects.filter(statut='active')
        .annotate(est_booste=Exists(boost_qs))
        .select_related('vendeur').prefetch_related('photos')
        .order_by('-est_booste', '-date_creation')[:6]
    )
    stats = {
        'total_annonces': Annonce.objects.filter(statut='active').count(),
        'total_vendeurs': Annonce.objects.filter(statut='active').values('vendeur').distinct().count(),
    }
    favoris_ids = set()
    if request.user.is_authenticated:
        favoris_ids = set(Favori.objects.filter(utilisateur=request.user).values_list('annonce_id', flat=True))
    return render(request, 'home.html', {'annonces_recentes': annonces_recentes, 'stats': stats, 'favoris_ids': favoris_ids})


def liste_annonces(request):
    form = FiltreAnnonceForm(request.GET)
    boost_qs = Boost.objects.filter(annonce=OuterRef('pk'), statut='actif', date_fin__gt=timezone.now())
    annonces = (
        Annonce.objects.filter(statut='active')
        .annotate(est_booste=Exists(boost_qs))
        .select_related('vendeur').prefetch_related('photos')
    )

    if form.is_valid():
        q = form.cleaned_data.get('q')
        region = form.cleaned_data.get('region')
        type_culture = form.cleaned_data.get('type_culture')
        type_titre = form.cleaned_data.get('type_titre_foncier')
        prix_max = form.cleaned_data.get('prix_max')
        surface_min = form.cleaned_data.get('surface_min')

        if q:
            annonces = annonces.filter(Q(titre__icontains=q) | Q(description__icontains=q) | Q(ville__icontains=q))
        if region:
            annonces = annonces.filter(region=region)
        if type_culture:
            annonces = annonces.filter(type_culture=type_culture)
        if type_titre:
            annonces = annonces.filter(type_titre_foncier=type_titre)
        if prix_max:
            annonces = annonces.filter(prix__lte=prix_max)
        if surface_min:
            annonces = annonces.filter(surface__gte=surface_min)

    # Markers carte — toutes les annonces, fallback coords région si pas de GPS
    markers = []
    for a in annonces.prefetch_related('photos'):
        if a.latitude and a.longitude:
            lat, lng, approx = float(a.latitude), float(a.longitude), False
        elif a.region in COORDS_REGIONS:
            lat, lng = COORDS_REGIONS[a.region]
            approx = True
        else:
            continue
        photo = a.photos.first()
        markers.append({
            'id': a.pk,
            'titre': a.titre,
            'ville': a.ville,
            'prix': str(a.prix),
            'surface': str(a.surface),
            'url': a.get_absolute_url(),
            'photo': photo.image.url if photo else None,
            'lat': lat,
            'lng': lng,
            'approx': approx,
        })

    annonces = annonces.order_by('-est_booste', '-date_creation')

    paginator = Paginator(annonces, 12)
    page = request.GET.get('page', 1)
    annonces_page = paginator.get_page(page)

    favoris_ids = set()
    if request.user.is_authenticated:
        favoris_ids = set(Favori.objects.filter(utilisateur=request.user).values_list('annonce_id', flat=True))

    return render(request, 'listings/liste.html', {
        'annonces': annonces_page,
        'form': form,
        'total': annonces.count(),
        'markers_json': json.dumps(markers, ensure_ascii=False),
        'favoris_ids': favoris_ids,
    })


def detail_annonce(request, pk):
    annonce = get_object_or_404(Annonce, pk=pk, statut='active')
    Annonce.objects.filter(pk=pk).update(vues=F('vues') + 1)
    if not request.user.is_authenticated or request.user != annonce.vendeur:
        VueAnnonce.objects.create(annonce=annonce)
    autres = list(
        Annonce.objects.filter(statut='active', region=annonce.region)
        .exclude(pk=pk)
        .prefetch_related('photos')[:3]
    )
    is_favori = False
    favoris_ids = set()
    if request.user.is_authenticated:
        is_favori = Favori.objects.filter(utilisateur=request.user, annonce=annonce).exists()
        autres_ids = [a.pk for a in autres]
        if autres_ids:
            favoris_ids = set(
                Favori.objects.filter(utilisateur=request.user, annonce_id__in=autres_ids)
                .values_list('annonce_id', flat=True)
            )

    share_url = request.build_absolute_uri(annonce.get_absolute_url())
    share_msg = (
        f"🌾 {annonce.titre}\n"
        f"📍 {annonce.ville} · {annonce.surface} ha · {int(annonce.prix):,} MAD\n"
        f"Découvrez cette annonce sur AgroTech :\n{share_url}"
    )
    share_wa_url = f"https://wa.me/?text={quote(share_msg)}"

    from accounts.models import Avis
    from django.db.models import Avg as DjAvg
    avis_vendeur = Avis.objects.filter(vendeur=annonce.vendeur)
    note_vendeur_raw = avis_vendeur.aggregate(avg=DjAvg('note'))['avg']
    note_vendeur = round(note_vendeur_raw, 1) if note_vendeur_raw is not None else None
    nb_avis_vendeur = avis_vendeur.count()

    return render(request, 'listings/detail.html', {
        'annonce': annonce,
        'autres': autres,
        'is_favori': is_favori,
        'favoris_ids': favoris_ids,
        'share_url': share_url,
        'share_wa_url': share_wa_url,
        'note_vendeur': note_vendeur,
        'nb_avis_vendeur': nb_avis_vendeur,
    })


@login_required
def creer_annonce(request):
    if request.method == 'POST':
        form = AnnonceForm(request.POST, request.FILES)
        photos = request.FILES.getlist('photos')
        photos_valides = _valider_photos(photos[:8])
        if form.is_valid():
            from django.db import transaction
            with transaction.atomic():
                annonce = form.save(commit=False)
                annonce.vendeur = request.user
                annonce.statut = Annonce.ACTIVE
                annonce.save()
                for i, photo in enumerate(photos_valides):
                    AnnoncePhoto.objects.create(annonce=annonce, image=photo, ordre=i)
            messages.success(request, 'Votre annonce a été publiée avec succès !')
            return redirect('listings:detail', pk=annonce.pk)
    else:
        form = AnnonceForm()
    return render(request, 'listings/creer.html', {'form': form})


@login_required
def modifier_annonce(request, pk):
    annonce = get_object_or_404(Annonce, pk=pk, vendeur=request.user)
    if request.method == 'POST':
        form = AnnonceForm(request.POST, request.FILES, instance=annonce)
        photos = request.FILES.getlist('photos')
        photos_valides = _valider_photos(photos[:8])
        if form.is_valid():
            form.save()
            for i, photo in enumerate(photos_valides):
                AnnoncePhoto.objects.create(annonce=annonce, image=photo, ordre=annonce.photos.count() + i)
            messages.success(request, 'Annonce mise à jour.')
            return redirect('listings:detail', pk=annonce.pk)
    else:
        form = AnnonceForm(instance=annonce)
    return render(request, 'listings/modifier.html', {'form': form, 'annonce': annonce})


@login_required
def supprimer_annonce(request, pk):
    annonce = get_object_or_404(Annonce, pk=pk, vendeur=request.user)
    if request.method == 'POST':
        annonce.delete()
        messages.success(request, 'Annonce supprimée.')
        return redirect('accounts:tableau_de_bord')
    return render(request, 'listings/supprimer.html', {'annonce': annonce})


@login_required
def commander_boost(request, pk):
    annonce = get_object_or_404(Annonce, pk=pk, vendeur=request.user, statut='active')
    boost_en_cours = annonce.boost_actif

    if request.method == 'POST':
        try:
            duree = int(request.POST.get('duree', 0))
        except (ValueError, TypeError):
            duree = 0

        if duree not in BOOST_TARIFS:
            messages.error(request, 'Forfait invalide.')
            return redirect('listings:boost_commander', pk=pk)

        boost = Boost.objects.create(
            annonce=annonce,
            vendeur=request.user,
            duree_jours=duree,
            prix_paye=BOOST_TARIFS[duree],
        )
        boost.activer()
        return redirect('listings:boost_confirmation', boost_pk=boost.pk)

    return render(request, 'listings/boost_commander.html', {
        'annonce': annonce,
        'packages': BOOST_PACKAGES,
        'boost_en_cours': boost_en_cours,
    })


@login_required
def boost_confirmation(request, boost_pk):
    boost = get_object_or_404(Boost, pk=boost_pk, vendeur=request.user)
    return render(request, 'listings/boost_confirmation.html', {'boost': boost})


def comparer_annonces(request):
    ids_str = request.GET.get('ids', '')
    ids = [int(p) for p in ids_str.split(',') if p.strip().isdigit()][:3]

    annonces = list(
        Annonce.objects.filter(pk__in=ids, statut='active')
        .prefetch_related('photos')
        .select_related('vendeur')
    )

    if len(annonces) < 2:
        messages.warning(request, 'Sélectionnez au moins 2 terrains à comparer.')
        return redirect('listings:liste')

    valid_prix_ha = [(a.pk, a.prix_par_hectare) for a in annonces if a.prix_par_hectare]
    valid_surface = [(a.pk, float(a.surface)) for a in annonces if a.surface]

    best_prix_ha_id = min(valid_prix_ha, key=lambda x: x[1])[0] if valid_prix_ha else None
    best_surface_id = max(valid_surface, key=lambda x: x[1])[0] if valid_surface else None

    favoris_ids = set()
    if request.user.is_authenticated:
        favoris_ids = set(
            Favori.objects.filter(utilisateur=request.user, annonce_id__in=ids)
            .values_list('annonce_id', flat=True)
        )

    return render(request, 'listings/comparer.html', {
        'annonces': annonces,
        'best_prix_ha_id': best_prix_ha_id,
        'best_surface_id': best_surface_id,
        'favoris_ids': favoris_ids,
    })


@login_required
@require_POST
def toggle_favori(request, pk):
    annonce = get_object_or_404(Annonce, pk=pk)
    favori, created = Favori.objects.get_or_create(utilisateur=request.user, annonce=annonce)
    if not created:
        favori.delete()
        is_favori = False
    else:
        is_favori = True
    return JsonResponse({'is_favori': is_favori, 'count': annonce.favoris.count()})


@login_required
def mes_favoris(request):
    favoris = list(
        Favori.objects
        .filter(utilisateur=request.user)
        .select_related('annonce__vendeur')
        .prefetch_related('annonce__photos')
    )
    favoris_ids = {f.annonce_id for f in favoris}
    return render(request, 'listings/mes_favoris.html', {'favoris': favoris, 'favoris_ids': favoris_ids})
