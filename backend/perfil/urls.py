from django.urls import path
from . import views

app_name = 'perfil'

urlpatterns = [
    path('', views.index, name='index'),
    path('editar/', views.edit_profile, name='edit'),  # nova rota de edição
]
