from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Avis


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'ville', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'ville')
    ordering = ('-date_joined',)
    fieldsets = UserAdmin.fieldsets + (
        ('Profil AgroTech', {'fields': ('role', 'telephone', 'ville', 'bio', 'photo_profil')}),
    )


@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'vendeur', 'note', 'extrait_commentaire', 'date_creation')
    list_filter = ('note',)
    search_fields = ('auteur__email', 'auteur__first_name', 'vendeur__email', 'commentaire')
    ordering = ('-date_creation',)
    raw_id_fields = ('auteur', 'vendeur')

    @admin.display(description='Commentaire')
    def extrait_commentaire(self, obj):
        return (obj.commentaire[:80] + '…') if len(obj.commentaire) > 80 else obj.commentaire
