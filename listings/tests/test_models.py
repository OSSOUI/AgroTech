import pytest
from decimal import Decimal
from conftest import AnnonceFactory, UserFactory
from listings.models import Annonce


@pytest.mark.django_db
class TestAnnonceModel:

    def test_prix_par_hectare_calcule_correctement(self):
        annonce = AnnonceFactory(prix=Decimal('500000'), surface=Decimal('10'))
        assert annonce.prix_par_hectare == 50000

    def test_prix_par_hectare_none_si_surface_zero(self):
        annonce = AnnonceFactory(surface=Decimal('0'))
        assert annonce.prix_par_hectare is None

    def test_str_retourne_titre(self):
        annonce = AnnonceFactory(titre='Terrain à Meknès')
        assert str(annonce) == 'Terrain à Meknès'

    def test_get_absolute_url_contient_pk(self):
        annonce = AnnonceFactory()
        assert str(annonce.pk) in annonce.get_absolute_url()

    def test_statut_par_defaut_active_via_factory(self):
        annonce = AnnonceFactory()
        assert annonce.statut == Annonce.ACTIVE

    def test_ordering_par_date_creation_desc(self):
        a1 = AnnonceFactory()
        a2 = AnnonceFactory()
        annonces = list(Annonce.objects.all())
        assert annonces[0].pk == a2.pk


@pytest.mark.django_db
class TestValidationPhotos:

    def test_extension_valide_acceptee(self):
        from listings.views import _valider_photos
        from django.core.files.uploadedfile import SimpleUploadedFile
        photo = SimpleUploadedFile('terrain.jpg', b'x' * 100, content_type='image/jpeg')
        assert len(_valider_photos([photo])) == 1

    def test_extension_invalide_rejetee(self):
        from listings.views import _valider_photos
        from django.core.files.uploadedfile import SimpleUploadedFile
        photo = SimpleUploadedFile('terrain.exe', b'x' * 100, content_type='application/octet-stream')
        assert len(_valider_photos([photo])) == 0

    def test_photo_trop_grande_rejetee(self):
        from listings.views import _valider_photos
        from django.core.files.uploadedfile import SimpleUploadedFile
        taille = 11 * 1024 * 1024
        photo = SimpleUploadedFile('terrain.jpg', b'x' * taille, content_type='image/jpeg')
        assert len(_valider_photos([photo])) == 0

    def test_limite_a_8_photos(self):
        from listings.views import _valider_photos
        from django.core.files.uploadedfile import SimpleUploadedFile
        photos = [
            SimpleUploadedFile(f'terrain{i}.jpg', b'x' * 100, content_type='image/jpeg')
            for i in range(10)
        ]
        result = _valider_photos(photos[:8])
        assert len(result) == 8
