import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import User
from conftest import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_client_auth(vendeur):
    client = APIClient()
    client.force_authenticate(user=vendeur)
    return client


@pytest.mark.django_db
class TestInscriptionAPI:

    def test_inscription_cree_utilisateur(self, api_client):
        response = api_client.post('/api/v1/auth/inscription/', {
            'email': 'nouveau@test.ma',
            'password': 'Motdepasse123!',
            'first_name': 'Karim',
            'last_name': 'Tahiri',
        })
        assert response.status_code == 201
        assert User.objects.filter(email='nouveau@test.ma').exists()

    def test_inscription_retourne_tokens(self, api_client):
        response = api_client.post('/api/v1/auth/inscription/', {
            'email': 'nouveau2@test.ma',
            'password': 'Motdepasse123!',
            'first_name': 'Sara',
            'last_name': 'Bennis',
        })
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_inscription_retourne_donnees_utilisateur(self, api_client):
        response = api_client.post('/api/v1/auth/inscription/', {
            'email': 'sara@test.ma',
            'password': 'Motdepasse123!',
            'first_name': 'Sara',
            'last_name': 'Bennis',
        })
        assert response.data['user']['email'] == 'sara@test.ma'

    def test_inscription_email_duplique_echoue(self, api_client, vendeur):
        response = api_client.post('/api/v1/auth/inscription/', {
            'email': vendeur.email,
            'password': 'Motdepasse123!',
            'first_name': 'Test',
            'last_name': 'User',
        })
        assert response.status_code == 400

    def test_inscription_mot_de_passe_court_echoue(self, api_client):
        response = api_client.post('/api/v1/auth/inscription/', {
            'email': 'court@test.ma',
            'password': '123',
            'first_name': 'A',
            'last_name': 'B',
        })
        assert response.status_code == 400

    def test_inscription_definit_username_sur_email(self, api_client):
        api_client.post('/api/v1/auth/inscription/', {
            'email': 'username@test.ma',
            'password': 'Motdepasse123!',
            'first_name': 'Test',
            'last_name': 'User',
        })
        user = User.objects.get(email='username@test.ma')
        assert user.username == 'username@test.ma'


@pytest.mark.django_db
class TestMoiAPI:

    def test_non_authentifie_retourne_401(self, api_client):
        response = api_client.get('/api/v1/auth/moi/')
        assert response.status_code == 401

    def test_retourne_email_pour_utilisateur_connecte(self, api_client_auth, vendeur):
        response = api_client_auth.get('/api/v1/auth/moi/')
        assert response.status_code == 200
        assert response.data['email'] == vendeur.email

    def test_ne_retourne_pas_email_dans_profil_public(self, api_client, vendeur):
        # Le profil vendeur public ne doit pas exposer l'email
        response = api_client.get(f'/api/v1/vendeurs/{vendeur.pk}/')
        assert response.status_code == 200
        assert 'email' not in response.data.get('vendeur', {})
