from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'ville', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'ville')
    ordering = ('-date_joined',)
    fieldsets = UserAdmin.fieldsets + (
        ('Profil AgroTech', {'fields': ('role', 'telephone', 'ville', 'bio', 'photo_profil')}),
    )
