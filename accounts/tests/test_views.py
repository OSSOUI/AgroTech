import pytest
from django.urls import reverse
from conftest import UserFactory, AvisFactory, ConversationFactory


@pytest.mark.django_db
class TestInscriptionView:

    def test_get_affiche_formulaire(self, client):
        url = reverse('accounts:inscription')
        response = client.get(url)
        assert response.status_code == 200

    def test_post_valide_cree_compte_et_redirige(self, client):
        url = reverse('accounts:inscription')
        response = client.post(url, {
            'first_name': 'Sara',
            'last_name': 'Idrissi',
            'email': 'sara@test.ma',
            'telephone': '0612345678',
            'ville': 'Fès',
            'password1': 'Motdepasse123!',
            'password2': 'Motdepasse123!',
        })
        assert response.status_code == 302
        from accounts.models import User
        assert User.objects.filter(email='sara@test.ma').exists()

    def test_utilisateur_connecte_redirige_vers_dashboard(self, client_vendeur):
        url = reverse('accounts:inscription')
        response = client_vendeur.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestConnexionView:

    def test_get_affiche_formulaire(self, client):
        response = client.get(reverse('accounts:connexion'))
        assert response.status_code == 200

    def test_connexion_valide_redirige(self, client, vendeur):
        response = client.post(reverse('accounts:connexion'), {
            'username': vendeur.email,
            'password': 'motdepasse123',
        })
        assert response.status_code == 302

    def test_mauvais_mot_de_passe_reste_sur_page(self, client, vendeur):
        response = client.post(reverse('accounts:connexion'), {
            'username': vendeur.email,
            'password': 'mauvaismdp',
        })
        assert response.status_code == 200

    def test_next_url_valide_redirige_correctement(self, client, vendeur):
        url = reverse('accounts:connexion') + '?next=/terrains/'
        response = client.post(url, {
            'username': vendeur.email,
            'password': 'motdepasse123',
        })
        assert response.status_code == 302
        assert response['Location'] == '/terrains/'

    def test_next_url_externe_ignoree(self, client, vendeur):
        url = reverse('accounts:connexion') + '?next=http://pirate.com'
        response = client.post(url, {
            'username': vendeur.email,
            'password': 'motdepasse123',
        })
        assert response.status_code == 302
        assert 'pirate.com' not in response['Location']


@pytest.mark.django_db
class TestTableauDeBordView:

    def test_redirige_si_non_connecte(self, client):
        response = client.get(reverse('accounts:tableau_de_bord'))
        assert response.status_code == 302

    def test_affiche_dashboard_pour_connecte(self, client_vendeur):
        response = client_vendeur.get(reverse('accounts:tableau_de_bord'))
        assert response.status_code == 200

    def test_contient_annonces_du_vendeur(self, client_vendeur, annonce):
        response = client_vendeur.get(reverse('accounts:tableau_de_bord'))
        assert annonce.titre in response.content.decode()


@pytest.mark.django_db
class TestProfilVendeurView:

    def test_profil_accessible_sans_connexion(self, client, vendeur):
        response = client.get(reverse('accounts:profil_vendeur', args=[vendeur.pk]))
        assert response.status_code == 200

    def test_profil_introuvable_retourne_404(self, client):
        response = client.get(reverse('accounts:profil_vendeur', args=[99999]))
        assert response.status_code == 404

    def test_peut_laisser_avis_si_conversation_existante(self, client_acheteur, conversation):
        vendeur = conversation.vendeur
        response = client_acheteur.get(reverse('accounts:profil_vendeur', args=[vendeur.pk]))
        assert response.context['peut_laisser_avis'] is True

    def test_ne_peut_pas_laisser_avis_sans_conversation(self, client_acheteur, vendeur):
        response = client_acheteur.get(reverse('accounts:profil_vendeur', args=[vendeur.pk]))
        assert response.context['peut_laisser_avis'] is False


@pytest.mark.django_db
class TestLaisserAvisView:

    def test_avis_cree_avec_donnees_valides(self, client_acheteur, conversation):
        vendeur = conversation.vendeur
        url = reverse('accounts:laisser_avis', kwargs={'vendeur_pk': vendeur.pk})
        response = client_acheteur.post(url, {'note': 4, 'commentaire': 'Super vendeur'})
        assert response.status_code == 302
        from accounts.models import Avis
        assert Avis.objects.filter(vendeur=vendeur).exists()

    def test_vendeur_ne_peut_pas_se_noter(self, client_vendeur, vendeur):
        url = reverse('accounts:laisser_avis', kwargs={'vendeur_pk': vendeur.pk})
        response = client_vendeur.post(url, {'note': 5})
        assert response.status_code == 302
        from accounts.models import Avis
        assert not Avis.objects.filter(vendeur=vendeur).exists()

    def test_note_invalide_refusee(self, client_acheteur, conversation):
        vendeur = conversation.vendeur
        url = reverse('accounts:laisser_avis', kwargs={'vendeur_pk': vendeur.pk})
        client_acheteur.post(url, {'note': 10})
        from accounts.models import Avis
        assert not Avis.objects.filter(vendeur=vendeur).exists()
