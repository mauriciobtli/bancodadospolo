from django.urls import path

from . import views

app_name = "importacao"

urlpatterns = [
    path("organizacoes/", views.importar_organizacoes, name="organizacoes"),
]
