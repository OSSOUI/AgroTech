from django.db import models
from django.conf import settings
from django.urls import reverse


REGIONS = [
    ('tanger-tetouan', 'Tanger-Tétouan-Al Hoceïma'),
    ('oriental', "L'Oriental"),
    ('fes-meknes', 'Fès-Meknès'),
    ('rabat-sale', 'Rabat-Salé-Kénitra'),
    ('beni-mellal', 'Béni Mellal-Khénifra'),
    ('casablanca', 'Casablanca-Settat'),
    ('marrakech', 'Marrakech-Safi'),
    ('draa-tafilalet', 'Drâa-Tafilalet'),
    ('souss-massa', 'Souss-Massa'),
    ('guelmim', 'Guelmim-Oued Noun'),
    ('laayoune', 'Laâyoune-Sakia El Hamra'),
    ('dakhla', 'Dakhla-Oued Ed Dahab'),
]

TYPES_CULTURE = [
    ('cereales', 'Céréales (blé, orge, maïs)'),
    ('maraichage', 'Maraîchage'),
    ('arboriculture', 'Arboriculture fruitière'),
    ('olivier', 'Olivier'),
    ('agrumes', 'Agrumes'),
    ('viticulture', 'Viticulture'),
    ('elevage', 'Élevage / Prairie'),
    ('polyculture', 'Polyculture'),
    ('autre', 'Autre'),
]

TYPES_TITRE = [
    ('melkia', 'Melkia (propriété privée)'),
    ('collectif', 'Collectif / Tribal'),
    ('domanial', 'Domanial'),
    ('en_cours', "En cours d'immatriculation"),
]


class Annonce(models.Model):
    ACTIVE = 'active'
    EN_ATTENTE = 'en_attente'
    DESACTIVEE = 'desactivee'
    STATUT_CHOICES = [
        (ACTIVE, 'Active'),
        (EN_ATTENTE, 'En attente'),
        (DESACTIVEE, 'Désactivée'),
    ]

    vendeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='annonces'
    )
    titre = models.CharField(max_length=200)
    description = models.TextField()
    region = models.CharField(max_length=50, choices=REGIONS)
    ville = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    surface = models.DecimalField(max_digits=10, decimal_places=2, help_text='Surface en hectares')
    prix = models.DecimalField(max_digits=14, decimal_places=2, help_text='Prix en MAD')
    type_culture = models.CharField(max_length=30, choices=TYPES_CULTURE)
    type_titre_foncier = models.CharField(max_length=20, choices=TYPES_TITRE)
    acces_eau = models.BooleanField(default=False, verbose_name="Accès à l'eau")
    acces_route = models.BooleanField(default=False, verbose_name='Accès route')
    electricite = models.BooleanField(default=False, verbose_name='Électricité')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default=EN_ATTENTE)
    vues = models.PositiveIntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Annonce'
        verbose_name_plural = 'Annonces'
        ordering = ['-date_creation']

    def __str__(self):
        return self.titre

    def get_absolute_url(self):
        return reverse('listings:detail', args=[self.pk])

    @property
    def prix_par_hectare(self):
        if self.surface and self.surface > 0:
            return int(self.prix / self.surface)
        return None

    def get_photo_principale(self):
        return self.photos.first()

    @property
    def is_boosted(self):
        from django.utils import timezone
        return self.boosts.filter(statut='actif', date_fin__gt=timezone.now()).exists()

    @property
    def boost_actif(self):
        from django.utils import timezone
        return self.boosts.filter(statut='actif', date_fin__gt=timezone.now()).first()


class AnnoncePhoto(models.Model):
    annonce = models.ForeignKey(Annonce, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='annonces/')
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return f'Photo {self.ordre} — {self.annonce.titre}'


class Boost(models.Model):
    PACKAGES = [(7, '7 jours'), (14, '14 jours'), (30, '30 jours')]
    TARIFS = {7: 199, 14: 349, 30: 599}
    STATUTS = [
        ('en_attente', 'En attente de paiement'),
        ('actif', 'Actif'),
        ('expire', 'Expiré'),
        ('annule', 'Annulé'),
    ]

    annonce = models.ForeignKey(Annonce, on_delete=models.CASCADE, related_name='boosts')
    vendeur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='boosts'
    )
    duree_jours = models.PositiveSmallIntegerField(choices=PACKAGES)
    prix_paye = models.DecimalField(max_digits=8, decimal_places=2)
    statut = models.CharField(max_length=15, choices=STATUTS, default='en_attente')
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    date_commande = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_commande']
        verbose_name = 'Boost'
        verbose_name_plural = 'Boosts'

    def __str__(self):
        return f'Boost {self.duree_jours}j — {self.annonce.titre}'

    def activer(self):
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        self.statut = 'actif'
        self.date_debut = now
        self.date_fin = now + timedelta(days=self.duree_jours)
        self.save(update_fields=['statut', 'date_debut', 'date_fin'])

    @property
    def est_actif(self):
        from django.utils import timezone
        return self.statut == 'actif' and bool(self.date_fin) and self.date_fin > timezone.now()

    @property
    def jours_restants(self):
        if not self.est_actif:
            return 0
        from django.utils import timezone
        return max(0, (self.date_fin - timezone.now()).days)


class VueAnnonce(models.Model):
    annonce = models.ForeignKey(Annonce, on_delete=models.CASCADE, related_name='historique_vues')
    date = models.DateField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['annonce', 'date'])]
        verbose_name = 'Vue (historique)'
        verbose_name_plural = 'Vues (historique)'


class Favori(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favoris'
    )
    annonce = models.ForeignKey(
        Annonce, on_delete=models.CASCADE, related_name='favoris'
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('utilisateur', 'annonce')
        ordering = ['-date_ajout']
        verbose_name = 'Favori'
        verbose_name_plural = 'Favoris'

    def __str__(self):
        return f'{self.utilisateur.get_full_name()} ❤ {self.annonce.titre}'
