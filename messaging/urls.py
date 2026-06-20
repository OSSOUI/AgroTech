from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:conv_pk>/', views.conversation, name='conversation'),
    path('demarrer/<int:annonce_pk>/', views.demarrer_conversation, name='demarrer'),
]
