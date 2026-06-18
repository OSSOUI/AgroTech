import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Annonce, AnnoncePhoto
from .forms import AnnonceForm, FiltreAnnonceForm


def home(request):
    annonces_recentes = Annonce.objects.filter(statut='active').select_related('vendeur').prefetch_related('photos')[:6]
    stats = {
        'total_annonces': Annonce.objects.filter(statut='active').count(),
        'total_vendeurs': Annonce.objects.filter(statut='active').values('vendeur').distinct().count(),
    }
    return render(request, 'home.html', {'annonces_recentes': annonces_recentes, 'stats': stats})


def liste_annonces(request):
    form = FiltreAnnonceForm(request.GET)
    annonces = Annonce.objects.filter(statut='active').select_related('vendeur').prefetch_related('photos')

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

    # Coordonnées pour la carte (toutes les annonces filtrées ayant lat/lon)
    markers = []
    for a in annonces.filter(latitude__isnull=False, longitude__isnull=False):
        photo = a.photos.first()
        markers.append({
            'id': a.pk,
            'titre': a.titre,
            'ville': a.ville,
            'prix': str(a.prix),
            'surface': str(a.surface),
            'url': a.get_absolute_url(),
            'photo': photo.image.url if photo else None,
            'lat': float(a.latitude),
            'lng': float(a.longitude),
        })

    paginator = Paginator(annonces, 12)
    page = request.GET.get('page', 1)
    annonces_page = paginator.get_page(page)

    return render(request, 'listings/liste.html', {
        'annonces': annonces_page,
        'form': form,
        'total': annonces.count(),
        'markers_json': json.dumps(markers, ensure_ascii=False),
    })


def detail_annonce(request, pk):
    annonce = get_object_or_404(Annonce, pk=pk, statut='active')
    Annonce.objects.filter(pk=pk).update(vues=annonce.vues + 1)
    autres = Annonce.objects.filter(
        statut='active', region=annonce.region
    ).exclude(pk=pk).prefetch_related('photos')[:3]
    return render(request, 'listings/detail.html', {
        'annonce': annonce,
        'autres': autres,
    })


@login_required
def creer_annonce(request):
    if request.method == 'POST':
        form = AnnonceForm(request.POST, request.FILES)
        photos = request.FILES.getlist('photos')
        if form.is_valid():
            annonce = form.save(commit=False)
            annonce.vendeur = request.user
            annonce.statut = Annonce.ACTIVE
            annonce.save()
            for i, photo in enumerate(photos[:8]):
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
        if form.is_valid():
            form.save()
            for i, photo in enumerate(photos[:8]):
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
