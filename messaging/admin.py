from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('expediteur', 'contenu', 'lu', 'date_envoi')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('annonce', 'acheteur', 'vendeur', 'date_modification')
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'expediteur', 'lu', 'date_envoi')
    list_filter = ('lu',)
