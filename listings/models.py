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



class AnnoncePhoto(models.Model):
    annonce = models.ForeignKey(Annonce, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='annonces/')
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return f'Photo {self.ordre} — {self.annonce.titre}'



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
