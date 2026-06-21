import pytest
from django.urls import reverse
from messaging.models import Conversation, Message
from conftest import MessageFactory


@pytest.mark.django_db
class TestInboxView:

    def test_redirige_si_non_connecte(self, client):
        response = client.get(reverse('messaging:inbox'))
        assert response.status_code == 302

    def test_affiche_conversations_du_vendeur(self, client_vendeur, conversation):
        response = client_vendeur.get(reverse('messaging:inbox'))
        assert response.status_code == 200

    def test_affiche_conversations_de_lacheteur(self, client_acheteur, conversation):
        response = client_acheteur.get(reverse('messaging:inbox'))
        assert response.status_code == 200

    def test_ne_montre_pas_conversations_des_autres(self, client, conversation):
        autre = __import__('conftest').UserFactory()
        client.force_login(autre)
        response = client.get(reverse('messaging:inbox'))
        assert response.status_code == 200
        convs = [cd['conv'] for cd in response.context['convs_data']]
        assert conversation not in convs


@pytest.mark.django_db
class TestConversationView:

    def test_acheteur_peut_voir_conversation(self, client_acheteur, conversation):
        response = client_acheteur.get(
            reverse('messaging:conversation', args=[conversation.pk])
        )
        assert response.status_code == 200

    def test_vendeur_peut_voir_conversation(self, client_vendeur, conversation):
        response = client_vendeur.get(
            reverse('messaging:conversation', args=[conversation.pk])
        )
        assert response.status_code == 200

    def test_tiers_redirige(self, client, conversation):
        autre = __import__('conftest').UserFactory()
        client.force_login(autre)
        response = client.get(
            reverse('messaging:conversation', args=[conversation.pk])
        )
        assert response.status_code == 302

    def test_messages_marques_comme_lus(self, client_vendeur, conversation, acheteur):
        msg = MessageFactory(conversation=conversation, expediteur=acheteur, lu=False)
        client_vendeur.get(reverse('messaging:conversation', args=[conversation.pk]))
        msg.refresh_from_db()
        assert msg.lu is True

    def test_post_envoie_message(self, client_acheteur, conversation):
        url = reverse('messaging:conversation', args=[conversation.pk])
        client_acheteur.post(url, {'contenu': 'Nouveau message de test'})
        assert Message.objects.filter(
            conversation=conversation,
            contenu='Nouveau message de test'
        ).exists()

    def test_message_vide_non_enregistre(self, client_acheteur, conversation):
        url = reverse('messaging:conversation', args=[conversation.pk])
        count_avant = Message.objects.filter(conversation=conversation).count()
        client_acheteur.post(url, {'contenu': '   '})
        assert Message.objects.filter(conversation=conversation).count() == count_avant


@pytest.mark.django_db
class TestDemarrerConversationView:

    def test_get_non_autorise(self, client_acheteur, annonce):
        response = client_acheteur.get(
            reverse('messaging:demarrer', args=[annonce.pk])
        )
        assert response.status_code == 405

    def test_post_cree_conversation_et_message(self, client_acheteur, annonce, acheteur):
        client_acheteur.post(
            reverse('messaging:demarrer', args=[annonce.pk]),
            {'contenu': 'Bonjour, je suis intéressé.'}
        )
        assert Conversation.objects.filter(annonce=annonce, acheteur=acheteur).exists()
        conv = Conversation.objects.get(annonce=annonce, acheteur=acheteur)
        assert Message.objects.filter(conversation=conv).exists()

    def test_vendeur_ne_peut_pas_se_contacter(self, client_vendeur, annonce):
        response = client_vendeur.post(
            reverse('messaging:demarrer', args=[annonce.pk]),
            {'contenu': 'Test auto-message'}
        )
        assert response.status_code == 302
        assert not Conversation.objects.filter(annonce=annonce, acheteur=annonce.vendeur).exists()

    def test_message_vide_ne_cree_pas_conversation(self, client_acheteur, annonce, acheteur):
        client_acheteur.post(
            reverse('messaging:demarrer', args=[annonce.pk]),
            {'contenu': ''}
        )
        assert not Conversation.objects.filter(annonce=annonce, acheteur=acheteur).exists()

    def test_redirige_si_non_connecte(self, client, annonce):
        response = client.post(
            reverse('messaging:demarrer', args=[annonce.pk]),
            {'contenu': 'Test'}
        )
        assert response.status_code == 302
