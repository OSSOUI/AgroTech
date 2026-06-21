import pytest
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.forms import InscriptionVendeurForm, ProfilForm


def _make_image(name='photo.jpg', fmt='JPEG', size_bytes=None):
    buf = BytesIO()
    img = Image.new('RGB', (10, 10), color=(100, 150, 200))
    img.save(buf, format=fmt)
    content = buf.getvalue()
    if size_bytes and size_bytes > len(content):
        content = content + b'x' * (size_bytes - len(content))
    return SimpleUploadedFile(name, content, content_type='image/jpeg')


@pytest.mark.django_db
class TestInscriptionVendeurForm:

    def _donnees_valides(self, **overrides):
        data = {
            'first_name': 'Youssef',
            'last_name': 'Alami',
            'email': 'youssef@test.ma',
            'telephone': '0612345678',
            'ville': 'Rabat',
            'password1': 'Motdepasse123!',
            'password2': 'Motdepasse123!',
        }
        data.update(overrides)
        return data

    def test_formulaire_valide_avec_donnees_correctes(self):
        form = InscriptionVendeurForm(data=self._donnees_valides())
        assert form.is_valid(), form.errors

    def test_email_unique_requis(self):
        from conftest import UserFactory
        UserFactory(email='youssef@test.ma', username='youssef@test.ma')
        form = InscriptionVendeurForm(data=self._donnees_valides())
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_mots_de_passe_differents_invalide(self):
        data = self._donnees_valides(password2='AutreMotdepasse123!')
        form = InscriptionVendeurForm(data=data)
        assert not form.is_valid()

    def test_save_definit_username_sur_email(self):
        form = InscriptionVendeurForm(data=self._donnees_valides())
        assert form.is_valid()
        user = form.save()
        assert user.username == 'youssef@test.ma'

    def test_save_definit_role_vendeur(self):
        from accounts.models import User
        form = InscriptionVendeurForm(data=self._donnees_valides())
        assert form.is_valid()
        user = form.save()
        assert user.role == User.VENDEUR


@pytest.mark.django_db
class TestProfilFormValidationPhoto:

    def test_photo_jpg_acceptee(self):
        from conftest import UserFactory
        user = UserFactory()
        form = ProfilForm(
            data={'first_name': 'A', 'last_name': 'B'},
            files={'photo_profil': _make_image('photo.jpg')},
            instance=user,
        )
        assert 'photo_profil' not in form.errors

    def test_photo_extension_invalide_refusee(self):
        from conftest import UserFactory
        user = UserFactory()
        form = ProfilForm(
            data={'first_name': 'A', 'last_name': 'B'},
            files={'photo_profil': SimpleUploadedFile('photo.exe', b'fakedata', content_type='application/octet-stream')},
            instance=user,
        )
        assert not form.is_valid()
        assert 'photo_profil' in form.errors

    def test_photo_trop_grande_refusee(self):
        from conftest import UserFactory
        user = UserFactory()
        taille_6mo = 6 * 1024 * 1024
        form = ProfilForm(
            data={'first_name': 'A', 'last_name': 'B'},
            files={'photo_profil': _make_image('photo.jpg', size_bytes=taille_6mo)},
            instance=user,
        )
        assert not form.is_valid()
        assert 'photo_profil' in form.errors
