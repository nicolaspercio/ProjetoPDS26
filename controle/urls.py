"""Rotas do aplicativo controle."""

from django.urls import path

from .views import (
    EquipamentoCreateView,
    EquipamentoListView,
    PessoaCreateView,
    PessoaListView,
)

app_name = "controle"

urlpatterns = [
    path("", EquipamentoListView.as_view(), name="equipamento_list"),
    path("equipamentos/novo/", EquipamentoCreateView.as_view(), name="equipamento_create"),
    path("pessoas/", PessoaListView.as_view(), name="pessoa_list"),
    path("pessoas/nova/", PessoaCreateView.as_view(), name="pessoa_create"),
]
