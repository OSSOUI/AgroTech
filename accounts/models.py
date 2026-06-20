from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models


class User(AbstractUser):
    VENDEUR = 'vendeur'
    VISITEUR = 'visiteur'
    ROLE_CHOICES = [(VENDEUR, 'Vendeur'), (VISITEUR, 'Visiteur')]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=VISITEUR)
    telephone = models.CharField(max_length=20, blank=True)
    ville = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    photo_profil = models.ImageField(upload_to='profils/', blank=True, null=True)
    date_modification = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f'{self.get_full_name()} ({self.email})'

    @property
    def is_vendeur(self):
        return self.role == self.VENDEUR

    def get_full_name(self):
        full = f'{self.first_name} {self.last_name}'.strip()
        return full or self.email

    @property
    def whatsapp_number(self):
        if not self.telephone:
            return None
        digits = ''.join(filter(str.isdigit, self.telephone))
        if digits.startswith('00'):
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 10:
            digits = '212' + digits[1:]
        elif not digits.startswith('212') and len(digits) == 9:
            digits = '212' + digits
        return digits if len(digits) >= 10 else None

    @property
    def note_moyenne(self):
        from django.db.models import Avg
        result = self.avis_recus.aggregate(avg=Avg('note'))
        avg = result['avg']
        return round(avg, 1) if avg is not None else None

    @property
    def nb_avis(self):
        return self.avis_recus.count()


class Avis(models.Model):
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='avis_donnes'
    )
    vendeur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='avis_recus'
    )
    note = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    commentaire = models.TextField(max_length=1000, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('auteur', 'vendeur')
        ordering = ['-date_creation']
        verbose_name = 'Avis'
        verbose_name_plural = 'Avis'

    def __str__(self):
        return f'{self.auteur.get_full_name()} → {self.vendeur.get_full_name()} : {self.note}/5'
