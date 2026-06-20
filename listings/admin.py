from django.contrib import admin
from django.utils import timezone
from .models import Annonce, AnnoncePhoto, Boost


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


def activer_boosts(modeladmin, request, queryset):
    for boost in queryset.filter(statut='en_attente'):
        boost.activer()
activer_boosts.short_description = 'Activer les boosts sélectionnés'


@admin.register(Boost)
class BoostAdmin(admin.ModelAdmin):
    list_display = ('annonce', 'vendeur', 'duree_jours', 'prix_paye', 'statut', 'date_debut', 'date_fin', 'date_commande')
    list_filter = ('statut', 'duree_jours')
    search_fields = ('annonce__titre', 'vendeur__email', 'vendeur__first_name')
    readonly_fields = ('date_commande',)
    actions = [activer_boosts]
    date_hierarchy = 'date_commande'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Auto-expire boosts dépassés
        qs.filter(statut='actif', date_fin__lt=timezone.now()).update(statut='expire')
        return qs
