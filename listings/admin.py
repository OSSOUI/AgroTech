from django.contrib import admin
from .models import Annonce, AnnoncePhoto


class AnnoncePhotoInline(admin.TabularInline):
    model = AnnoncePhoto
    extra = 1


@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'vendeur', 'region', 'ville', 'surface', 'prix', 'statut', 'vues', 'date_creation')
    list_filter = ('statut', 'region', 'type_culture', 'type_titre_foncier')
    search_fields = ('titre', 'description', 'ville', 'vendeur__email')
    list_editable = ('statut',)
    inlines = [AnnoncePhotoInline]
    date_hierarchy = 'date_creation'


@admin.register(AnnoncePhoto)
class AnnoncePhotoAdmin(admin.ModelAdmin):
    list_display = ('annonce', 'ordre', 'image')
    list_filter = ('annonce',)
