import pytest
from rest_framework.test import APIClient
from listings.models import Favori
from conftest import AnnonceFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_client_auth(vendeur):
    client = APIClient()
    client.force_authenticate(user=vendeur)
    return client


@pytest.fixture
def api_client_acheteur(acheteur):
    client = APIClient()
    client.force_authenticate(user=acheteur)
    return client


@pytest.mark.django_db
class TestAnnonceListAPI:

    def test_accessible_sans_authentification(self, api_client):
        response = api_client.get('/api/v1/annonces/')
        assert response.status_code == 200

    def test_retourne_uniquement_annonces_actives(self, api_client, annonce, annonce_inactive):
        response = api_client.get('/api/v1/annonces/')
        titres = [a['titre'] for a in response.data['results']]
        assert annonce.titre in titres
        assert annonce_inactive.titre not in titres

    def test_filtre_par_region(self, api_client, annonce):
        response = api_client.get('/api/v1/annonces/', {'region': 'casablanca'})
        assert response.status_code == 200
        assert all(a['region'] == 'casablanca' for a in response.data['results'])

    def test_filtre_par_prix_max(self, api_client, annonce):
        prix_max = int(annonce.prix) - 1
        response = api_client.get('/api/v1/annonces/', {'prix_max': prix_max})
        titres = [a['titre'] for a in response.data['results']]
        assert annonce.titre not in titres

    def test_email_vendeur_non_expose(self, api_client, annonce):
        response = api_client.get('/api/v1/annonces/')
        vendeur_data = response.data['results'][0]['vendeur']
        assert 'email' not in vendeur_data
        assert 'telephone' not in vendeur_data

    def test_pagination_presente(self, api_client):
        response = api_client.get('/api/v1/annonces/')
        assert 'results' in response.data
        assert 'count' in response.data


@pytest.mark.django_db
class TestAnnonceDetailAPI:

    def test_accessible_sans_authentification(self, api_client, annonce):
        response = api_client.get(f'/api/v1/annonces/{annonce.pk}/')
        assert response.status_code == 200

    def test_annonce_inactive_retourne_404(self, api_client, annonce_inactive):
        response = api_client.get(f'/api/v1/annonces/{annonce_inactive.pk}/')
        assert response.status_code == 404

    def test_incremente_compteur_vues(self, api_client, annonce):
        vues_avant = annonce.vues
        api_client.get(f'/api/v1/annonces/{annonce.pk}/')
        annonce.refresh_from_db()
        assert annonce.vues == vues_avant + 1


@pytest.mark.django_db
class TestFavoriAPI:

    def test_toggle_ajoute_favori(self, api_client_acheteur, annonce, acheteur):
        response = api_client_acheteur.post(f'/api/v1/favoris/{annonce.pk}/toggle/')
        assert response.status_code == 200
        assert response.data['is_favori'] is True
        assert Favori.objects.filter(utilisateur=acheteur, annonce=annonce).exists()

    def test_toggle_retire_favori_existant(self, api_client_acheteur, annonce, acheteur):
        Favori.objects.create(utilisateur=acheteur, annonce=annonce)
        response = api_client_acheteur.post(f'/api/v1/favoris/{annonce.pk}/toggle/')
        assert response.data['is_favori'] is False
        assert not Favori.objects.filter(utilisateur=acheteur, annonce=annonce).exists()

    def test_favoris_non_connecte_retourne_401(self, api_client, annonce):
        response = api_client.post(f'/api/v1/favoris/{annonce.pk}/toggle/')
        assert response.status_code == 401

    def test_liste_favoris_retourne_annonces(self, api_client_acheteur, annonce, acheteur):
        Favori.objects.create(utilisateur=acheteur, annonce=annonce)
        response = api_client_acheteur.get('/api/v1/favoris/')
        assert response.status_code == 200
        titres = [a['titre'] for a in response.data['results']]
        assert annonce.titre in titres
