"""Rotas do aplicativo controle."""

from django.urls import path

from .views import (
    DevolucaoCreateView,
    EmprestimoCreateView,
    EmprestimoListView,
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
    path("emprestimos/", EmprestimoListView.as_view(), name="emprestimo_list"),
    path("emprestimos/novo/", EmprestimoCreateView.as_view(), name="emprestimo_create"),
    path("devolucoes/", DevolucaoCreateView.as_view(), name="devolucao_create"),
]
