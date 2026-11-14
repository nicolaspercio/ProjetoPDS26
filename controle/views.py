"""Views baseadas em classes (CBVs) para US01, US02 e US03."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .forms import EquipamentoForm, PessoaForm
from .models import Equipamento, Pessoa
from .services import CadastroPessoasService, CatalogoEquipamentosService


class EquipamentoListView(ListView):
    """Exibe e filtra equipamentos disponíveis e emprestados (US03)."""

    model = Equipamento
    template_name = "controle/equipamento_list.html"
    context_object_name = "equipamentos"
    service = CatalogoEquipamentosService()
    SITUACOES_VALIDAS = {"todos", "disponiveis", "emprestados"}

    def _situacao_atual(self) -> str:
        situacao = self.request.GET.get("situacao", "todos").strip()
        if situacao not in self.SITUACOES_VALIDAS:
            return "todos"
        return situacao

    def get_queryset(self):
        busca = self.request.GET.get("q", "")
        situacao = self._situacao_atual()
        return self.service.listar(busca=busca, situacao=situacao)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["busca"] = self.request.GET.get("q", "").strip()
        context["situacao"] = self._situacao_atual()
        context["resumo"] = self.service.resumo_disponibilidade()
        context["secao_ativa"] = "equipamentos"
        return context


class EquipamentoCreateView(CreateView):
    """Realiza o cadastro de novos equipamentos no laboratório (US01)."""

    model = Equipamento
    form_class = EquipamentoForm
    template_name = "controle/equipamento_form.html"
    success_url = reverse_lazy("controle:equipamento_list")
    service = CatalogoEquipamentosService()

    def form_valid(self, form):
        try:
            self.object = self.service.cadastrar(
                nome=form.cleaned_data["nome"],
                codigo=form.cleaned_data["codigo"],
                descricao=form.cleaned_data.get("descricao", ""),
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"Equipamento '{self.object.nome}' ({self.object.codigo}) cadastrado com sucesso.",
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["secao_ativa"] = "novo_equipamento"
        return context


class PessoaListView(ListView):
    """Lista pessoas cadastradas e prontas para seleção de empréstimo (US02)."""

    model = Pessoa
    template_name = "controle/pessoa_list.html"
    context_object_name = "pessoas"
    service = CadastroPessoasService()

    def get_queryset(self):
        busca = self.request.GET.get("q", "")
        return self.service.listar(busca=busca)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["busca"] = self.request.GET.get("q", "").strip()
        context["total_pessoas"] = self.service.contar()
        context["pessoas_selecao"] = self.service.listar_para_selecao()
        context["secao_ativa"] = "pessoas"
        return context


class PessoaCreateView(CreateView):
    """Realiza o cadastro de novas pessoas autorizadas (US02)."""

    model = Pessoa
    form_class = PessoaForm
    template_name = "controle/pessoa_form.html"
    success_url = reverse_lazy("controle:pessoa_list")
    service = CadastroPessoasService()

    def form_valid(self, form):
        try:
            self.object = self.service.cadastrar(
                nome=form.cleaned_data["nome"],
                identificador=form.cleaned_data["identificador"],
                contato=form.cleaned_data["contato"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"Pessoa '{self.object.nome}' ({self.object.identificador}) cadastrada com sucesso.",
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["secao_ativa"] = "nova_pessoa"
        return context
