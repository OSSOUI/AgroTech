import pytest
from conftest import UserFactory, AvisFactory


@pytest.mark.django_db
class TestUserModel:

    def test_get_full_name_retourne_prenom_nom(self):
        user = UserFactory(first_name='Ahmed', last_name='Benali')
        assert user.get_full_name() == 'Ahmed Benali'

    def test_get_full_name_retourne_email_si_vide(self):
        user = UserFactory(first_name='', last_name='')
        assert user.get_full_name() == user.email

    def test_is_vendeur_vrai_pour_role_vendeur(self):
        from accounts.models import User
        user = UserFactory(role=User.VENDEUR)
        assert user.is_vendeur is True

    def test_is_vendeur_faux_pour_visiteur(self):
        from accounts.models import User
        user = UserFactory(role=User.VISITEUR)
        assert user.is_vendeur is False

    def test_whatsapp_number_convertit_format_marocain(self):
        user = UserFactory(telephone='0612345678')
        assert user.whatsapp_number == '212612345678'

    def test_whatsapp_number_none_si_pas_de_telephone(self):
        user = UserFactory(telephone='')
        assert user.whatsapp_number is None

    def test_whatsapp_number_conserve_prefixe_212(self):
        user = UserFactory(telephone='+212612345678')
        assert user.whatsapp_number == '212612345678'

    def test_note_moyenne_none_sans_avis(self):
        user = UserFactory()
        assert user.note_moyenne is None

    def test_note_moyenne_calculee_correctement(self):
        vendeur = UserFactory()
        AvisFactory(vendeur=vendeur, note=4)
        AvisFactory(vendeur=vendeur, note=2)
        assert vendeur.note_moyenne == 3.0

    def test_nb_avis_zero_sans_avis(self):
        user = UserFactory()
        assert user.nb_avis == 0

    def test_nb_avis_compte_les_avis_recus(self):
        vendeur = UserFactory()
        AvisFactory(vendeur=vendeur)
        AvisFactory(vendeur=vendeur)
        assert vendeur.nb_avis == 2

    def test_str_contient_email(self):
        user = UserFactory(email='test@test.ma')
        assert 'test@test.ma' in str(user)
