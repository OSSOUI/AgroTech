import pytest
from django.urls import reverse
from listings.models import Annonce, Favori, VueAnnonce
from conftest import AnnonceFactory, UserFactory


@pytest.mark.django_db
class TestListeAnnoncesView:

    def test_page_accessible_sans_connexion(self, client):
        response = client.get(reverse('listings:liste'))
        assert response.status_code == 200

    def test_affiche_annonces_actives_seulement(self, client, annonce, annonce_inactive):
        response = client.get(reverse('listings:liste'))
        content = response.content.decode()
        assert annonce.titre in content
        assert annonce_inactive.titre not in content

    def test_filtre_par_region(self, client, annonce):
        response = client.get(reverse('listings:liste'), {'region': 'casablanca'})
        assert annonce.titre in response.content.decode()

    def test_filtre_par_region_sans_resultat(self, client, annonce):
        response = client.get(reverse('listings:liste'), {'region': 'dakhla'})
        assert annonce.titre not in response.content.decode()

    def test_filtre_par_recherche_titre(self, client, annonce):
        response = client.get(reverse('listings:liste'), {'q': annonce.titre[:10]})
        assert annonce.titre in response.content.decode()


@pytest.mark.django_db
class TestDetailAnnonceView:

    def test_page_accessible_sans_connexion(self, client, annonce):
        response = client.get(reverse('listings:detail', args=[annonce.pk]))
        assert response.status_code == 200

    def test_annonce_inactive_retourne_404(self, client, annonce_inactive):
        response = client.get(reverse('listings:detail', args=[annonce_inactive.pk]))
        assert response.status_code == 404

    def test_vue_incrementee_a_chaque_visite(self, client, annonce):
        vues_avant = annonce.vues
        client.get(reverse('listings:detail', args=[annonce.pk]))
        annonce.refresh_from_db()
        assert annonce.vues == vues_avant + 1

    def test_vue_annonce_creee_pour_visiteur(self, client, annonce):
        client.get(reverse('listings:detail', args=[annonce.pk]))
        assert VueAnnonce.objects.filter(annonce=annonce).exists()


@pytest.mark.django_db
class TestCreerAnnonceView:

    def test_redirige_si_non_connecte(self, client):
        response = client.get(reverse('listings:creer'))
        assert response.status_code == 302

    def test_get_affiche_formulaire(self, client_vendeur):
        response = client_vendeur.get(reverse('listings:creer'))
        assert response.status_code == 200

    def test_post_valide_cree_annonce(self, client_vendeur):
        data = {
            'titre': 'Nouveau terrain',
            'description': 'Description du terrain agricole.',
            'region': 'fes-meknes',
            'ville': 'Meknès',
            'surface': '8.5',
            'prix': '350000',
            'type_culture': 'maraichage',
            'type_titre_foncier': 'melkia',
            'acces_eau': True,
        }
        response = client_vendeur.post(reverse('listings:creer'), data)
        assert response.status_code == 302
        assert Annonce.objects.filter(titre='Nouveau terrain').exists()

    def test_annonce_creee_avec_statut_active(self, client_vendeur):
        data = {
            'titre': 'Terrain actif',
            'description': 'Description.',
            'region': 'casablanca',
            'ville': 'Casa',
            'surface': '5',
            'prix': '200000',
            'type_culture': 'cereales',
            'type_titre_foncier': 'melkia',
        }
        client_vendeur.post(reverse('listings:creer'), data)
        annonce = Annonce.objects.get(titre='Terrain actif')
        assert annonce.statut == Annonce.ACTIVE


@pytest.mark.django_db
class TestModifierAnnonceView:

    def test_redirige_si_non_connecte(self, client, annonce):
        response = client.get(reverse('listings:modifier', args=[annonce.pk]))
        assert response.status_code == 302

    def test_autre_vendeur_ne_peut_pas_modifier(self, client, annonce):
        autre = UserFactory()
        client.force_login(autre)
        response = client.get(reverse('listings:modifier', args=[annonce.pk]))
        assert response.status_code == 404

    def test_proprietaire_peut_modifier(self, client_vendeur, annonce):
        response = client_vendeur.get(reverse('listings:modifier', args=[annonce.pk]))
        assert response.status_code == 200


@pytest.mark.django_db
class TestSupprimerAnnonceView:

    def test_post_supprime_annonce(self, client_vendeur, annonce):
        pk = annonce.pk
        client_vendeur.post(reverse('listings:supprimer', args=[pk]))
        assert not Annonce.objects.filter(pk=pk).exists()

    def test_get_affiche_confirmation(self, client_vendeur, annonce):
        response = client_vendeur.get(reverse('listings:supprimer', args=[annonce.pk]))
        assert response.status_code == 200

    def test_autre_vendeur_ne_peut_pas_supprimer(self, client, annonce):
        autre = UserFactory()
        client.force_login(autre)
        response = client.post(reverse('listings:supprimer', args=[annonce.pk]))
        assert response.status_code == 404
        assert Annonce.objects.filter(pk=annonce.pk).exists()


@pytest.mark.django_db
class TestToggleFavoriView:

    def test_redirige_si_non_connecte(self, client, annonce):
        response = client.post(reverse('listings:toggle_favori', args=[annonce.pk]))
        assert response.status_code == 302

    def test_ajoute_favori(self, client_acheteur, annonce, acheteur):
        client_acheteur.post(reverse('listings:toggle_favori', args=[annonce.pk]))
        assert Favori.objects.filter(utilisateur=acheteur, annonce=annonce).exists()

    def test_retire_favori_si_deja_present(self, client_acheteur, annonce, acheteur):
        Favori.objects.create(utilisateur=acheteur, annonce=annonce)
        client_acheteur.post(reverse('listings:toggle_favori', args=[annonce.pk]))
        assert not Favori.objects.filter(utilisateur=acheteur, annonce=annonce).exists()

    def test_get_non_autorise(self, client_acheteur, annonce):
        response = client_acheteur.get(reverse('listings:toggle_favori', args=[annonce.pk]))
        assert response.status_code == 405


@pytest.mark.django_db
class TestComparerView:

    def test_moins_de_2_annonces_redirige(self, client, annonce):
        response = client.get(reverse('listings:comparer'), {'ids': str(annonce.pk)})
        assert response.status_code == 302

    def test_2_annonces_affiche_comparaison(self, client, vendeur):
        a1 = AnnonceFactory(vendeur=vendeur)
        a2 = AnnonceFactory(vendeur=vendeur)
        response = client.get(reverse('listings:comparer'), {'ids': f'{a1.pk},{a2.pk}'})
        assert response.status_code == 200
