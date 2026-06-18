from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.liste_annonces, name='liste'),
    path('<int:pk>/', views.detail_annonce, name='detail'),
    path('deposer/', views.creer_annonce, name='creer'),
    path('<int:pk>/modifier/', views.modifier_annonce, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer_annonce, name='supprimer'),
]
