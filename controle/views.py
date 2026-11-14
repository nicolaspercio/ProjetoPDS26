"""Views baseadas em classes (CBVs) para US01, US02 e US03."""

from django.contrib import messages
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

    def get_queryset(self):
        busca = self.request.GET.get("q", "")
        situacao = self.request.GET.get("situacao", "todos")
        return self.service.listar(busca=busca, situacao=situacao)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["busca"] = self.request.GET.get("q", "").strip()
        context["situacao"] = self.request.GET.get("situacao", "todos")
        context["resumo"] = self.service.resumo_disponibilidade()
        context["secao_ativa"] = "equipamentos"
        return context


class EquipamentoCreateView(CreateView):
    """Realiza o cadastro de novos equipamentos no laboratório (US01)."""

    model = Equipamento
    form_class = EquipamentoForm
    template_name = "controle/equipamento_form.html"
    success_url = reverse_lazy("controle:equipamento_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Equipamento '{self.object.nome}' ({self.object.codigo}) cadastrado com sucesso.",
        )
        return response

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
        context["total_pessoas"] = Pessoa.objects.count()
        context["pessoas_selecao"] = self.service.listar_para_selecao()
        context["secao_ativa"] = "pessoas"
        return context


class PessoaCreateView(CreateView):
    """Realiza o cadastro de novas pessoas autorizadas (US02)."""

    model = Pessoa
    form_class = PessoaForm
    template_name = "controle/pessoa_form.html"
    success_url = reverse_lazy("controle:pessoa_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Pessoa '{self.object.nome}' ({self.object.identificador}) cadastrada com sucesso.",
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["secao_ativa"] = "nova_pessoa"
        return context
