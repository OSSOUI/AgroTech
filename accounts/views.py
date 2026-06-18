from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .forms import InscriptionVendeurForm, ConnexionForm, ProfilForm
from listings.models import Annonce


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
            next_url = request.GET.get('next', 'accounts:tableau_de_bord')
            return redirect(next_url)
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
    annonces = Annonce.objects.filter(vendeur=request.user).order_by('-date_creation')
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
            form.save()
            messages.success(request, 'Votre profil a été mis à jour.')
            return redirect('accounts:profil')
    else:
        form = ProfilForm(instance=request.user)
    return render(request, 'accounts/profil.html', {'form': form})
