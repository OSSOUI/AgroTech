from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.liste_annonces, name='liste'),
    path('<int:pk>/', views.detail_annonce, name='detail'),
    path('deposer/', views.creer_annonce, name='creer'),
    path('<int:pk>/modifier/', views.modifier_annonce, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer_annonce, name='supprimer'),
    path('<int:pk>/favori/', views.toggle_favori, name='toggle_favori'),
    path('mes-favoris/', views.mes_favoris, name='mes_favoris'),
    path('comparer/', views.comparer_annonces, name='comparer'),
    path('<int:pk>/boost/', views.commander_boost, name='boost_commander'),
    path('boost/<int:boost_pk>/confirmation/', views.boost_confirmation, name='boost_confirmation'),
]
