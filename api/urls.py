from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────
    path('auth/inscription/', views.InscriptionView.as_view(), name='api-inscription'),
    path('auth/connexion/', TokenObtainPairView.as_view(), name='api-connexion'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('auth/moi/', views.MoiView.as_view(), name='api-moi'),

    # ── Annonces ──────────────────────────────────────────────────
    path('annonces/', views.AnnonceListView.as_view(), name='api-annonces'),
    path('annonces/<int:pk>/', views.AnnonceDetailView.as_view(), name='api-annonce-detail'),

    # ── Favoris ───────────────────────────────────────────────────
    path('favoris/', views.FavorisView.as_view(), name='api-favoris'),
    path('favoris/<int:pk>/toggle/', views.toggle_favori, name='api-toggle-favori'),

    # ── Mes annonces ──────────────────────────────────────────────
    path('mes-annonces/', views.MesAnnoncesView.as_view(), name='api-mes-annonces'),

    # ── Vendeurs ──────────────────────────────────────────────────
    path('vendeurs/<int:pk>/', views.ProfilVendeurView.as_view(), name='api-vendeur'),
    path('vendeurs/<int:vendeur_pk>/avis/', views.laisser_avis, name='api-avis'),

    # ── Messagerie ────────────────────────────────────────────────
    path('conversations/', views.ConversationsView.as_view(), name='api-conversations'),
    path('conversations/<int:conv_id>/messages/', views.MessagesView.as_view(), name='api-messages'),
    path('annonces/<int:annonce_pk>/contacter/', views.envoyer_message, name='api-contacter'),
]
