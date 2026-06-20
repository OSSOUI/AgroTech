from django.db import models
from django.conf import settings


class Conversation(models.Model):
    annonce = models.ForeignKey(
        'listings.Annonce', on_delete=models.CASCADE, related_name='conversations'
    )
    acheteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_acheteur'
    )
    vendeur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_vendeur'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('annonce', 'acheteur')
        ordering = ['-date_modification']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'

    def __str__(self):
        return f'{self.acheteur.get_full_name()} ↔ {self.annonce.titre}'

    def dernier_message(self):
        return self.messages.order_by('-date_envoi').first()

    def non_lus_pour(self, user):
        return self.messages.filter(lu=False).exclude(expediteur=user).count()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('messaging:conversation', args=[self.pk])


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    expediteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_envoyes'
    )
    contenu = models.TextField(max_length=2000)
    lu = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_envoi']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return f'{self.expediteur.get_full_name()} — {self.date_envoi:%d/%m %H:%M}'
