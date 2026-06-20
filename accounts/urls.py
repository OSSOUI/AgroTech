from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('tableau-de-bord/', views.tableau_de_bord, name='tableau_de_bord'),
    path('profil/', views.profil, name='profil'),
    path('analytiques/', views.analytics_vendeur, name='analytics'),
    path('vendeur/<int:pk>/', views.profil_vendeur, name='profil_vendeur'),
    path('vendeur/<int:pk>/avis/', views.laisser_avis, name='laisser_avis'),
]
