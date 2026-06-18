from django.contrib.auth.models import AbstractUser
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
        """Retourne le numéro au format international sans + ni espaces (ex: 212661234567)."""
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
