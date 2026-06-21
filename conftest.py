import pytest
import factory
from django.test import Client
from accounts.models import User, Avis
from listings.models import Annonce, AnnoncePhoto, Favori, VueAnnonce
from messaging.models import Conversation, Message


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Sequence(lambda n: f'Prénom{n}')
    last_name = factory.Sequence(lambda n: f'Nom{n}')
    email = factory.Sequence(lambda n: f'user{n}@test.ma')
    username = factory.LazyAttribute(lambda o: o.email)
    password = factory.PostGenerationMethodCall('set_password', 'motdepasse123')
    role = User.VENDEUR
    telephone = '0612345678'
    ville = 'Casablanca'


class AnnonceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Annonce

    vendeur = factory.SubFactory(UserFactory)
    titre = factory.Sequence(lambda n: f'Terrain agricole #{n}')
    description = 'Belle parcelle avec accès eau et route.'
    region = 'casablanca'
    ville = 'Casablanca'
    surface = factory.Sequence(lambda n: 5 + n)
    prix = factory.Sequence(lambda n: 500_000 + n * 10_000)
    type_culture = 'cereales'
    type_titre_foncier = 'melkia'
    acces_eau = True
    acces_route = True
    electricite = False
    statut = Annonce.ACTIVE


class ConversationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Conversation

    annonce = factory.SubFactory(AnnonceFactory)
    acheteur = factory.SubFactory(UserFactory)
    vendeur = factory.LazyAttribute(lambda o: o.annonce.vendeur)


class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Message

    conversation = factory.SubFactory(ConversationFactory)
    expediteur = factory.LazyAttribute(lambda o: o.conversation.acheteur)
    contenu = 'Bonjour, je suis intéressé par votre terrain.'


class AvisFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Avis

    auteur = factory.SubFactory(UserFactory)
    vendeur = factory.SubFactory(UserFactory)
    note = 4
    commentaire = 'Très bon vendeur, réactif.'


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def vendeur(db):
    return UserFactory(email='vendeur@test.ma', username='vendeur@test.ma')


@pytest.fixture
def acheteur(db):
    return UserFactory(email='acheteur@test.ma', username='acheteur@test.ma', role=User.VISITEUR)


@pytest.fixture
def annonce(db, vendeur):
    return AnnonceFactory(vendeur=vendeur)


@pytest.fixture
def annonce_inactive(db, vendeur):
    return AnnonceFactory(vendeur=vendeur, statut=Annonce.DESACTIVEE)


@pytest.fixture
def conversation(db, annonce, acheteur):
    return ConversationFactory(annonce=annonce, acheteur=acheteur, vendeur=annonce.vendeur)


@pytest.fixture
def client_vendeur(client, vendeur):
    client.force_login(vendeur)
    return client


@pytest.fixture
def client_acheteur(client, acheteur):
    client.force_login(acheteur)
    return client
