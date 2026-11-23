"""Views baseadas em classes (CBVs) para cadastros, consultas, empréstimos e devoluções."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, ListView

from .forms import DevolucaoForm, EmprestimoForm, EquipamentoForm, PessoaForm
from .models import Emprestimo, Equipamento, Pessoa
from .services import (
    CadastroPessoasService,
    CatalogoEquipamentosService,
    EmprestimoService,
)


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


class EmprestimoListView(ListView):
    """Lista apenas empréstimos em andamento com pesquisa por pessoa ou equipamento (US06)."""

    model = Emprestimo
    template_name = "controle/emprestimo_list.html"
    context_object_name = "emprestimos"
    service = EmprestimoService()

    def get_queryset(self):
        busca = self.request.GET.get("q", "")
        return self.service.listar_em_andamento(busca=busca)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["busca"] = self.request.GET.get("q", "").strip()
        context["total_em_andamento"] = self.service.contar_em_andamento()
        context["secao_ativa"] = "emprestimos"
        return context


class EmprestimoCreateView(CreateView):
    """Registra um novo empréstimo de equipamento disponível (US04)."""

    model = Emprestimo
    form_class = EmprestimoForm
    template_name = "controle/emprestimo_form.html"
    success_url = reverse_lazy("controle:emprestimo_list")
    service = EmprestimoService()

    def form_valid(self, form):
        try:
            self.object = self.service.registrar_emprestimo(
                equipamento=form.cleaned_data["equipamento"],
                pessoa=form.cleaned_data["pessoa"],
                data_retirada=form.cleaned_data["data_retirada"],
                prazo_devolucao=form.cleaned_data["prazo_devolucao"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"Empréstimo de '{self.object.equipamento}' para '{self.object.pessoa}' registrado com sucesso.",
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["secao_ativa"] = "novo_emprestimo"
        return context


class DevolucaoCreateView(FormView):
    """Registra a devolução de um empréstimo em aberto (US05)."""

    form_class = DevolucaoForm
    template_name = "controle/devolucao_form.html"
    success_url = reverse_lazy("controle:emprestimo_list")
    service = EmprestimoService()

    def get_initial(self):
        initial = super().get_initial()
        emprestimo_id = self.request.GET.get("emprestimo")
        if emprestimo_id and emprestimo_id.isdigit():
            initial["emprestimo"] = int(emprestimo_id)
        return initial

    def form_valid(self, form):
        try:
            registro = self.service.registrar_devolucao(
                emprestimo=form.cleaned_data["emprestimo"],
                data_devolucao=form.cleaned_data["data_devolucao"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"Devolução de '{registro.equipamento}' registrada com sucesso. O equipamento voltou a ficar disponível.",
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_em_andamento"] = self.service.contar_em_andamento()
        context["secao_ativa"] = "devolucao"
        return context


class EmprestimoAtrasadoListView(ListView):
    """Lista empréstimos em aberto cujo prazo de devolução já venceu (US07)."""

    model = Emprestimo
    template_name = "controle/atraso_list.html"
    context_object_name = "atrasados"
    service = EmprestimoService()

    def get_queryset(self):
        busca = self.request.GET.get("q", "")
        return self.service.listar_atrasados(busca=busca)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["busca"] = self.request.GET.get("q", "").strip()
        context["total_atrasados"] = self.service.contar_atrasados()
        context["secao_ativa"] = "atrasos"
        return context


class HistoricoEmprestimoListView(ListView):
    """Lista todo o histórico de empréstimos com filtros por equipamento, pessoa e situação (US08)."""

    model = Emprestimo
    template_name = "controle/historico_list.html"
    context_object_name = "emprestimos"
    service = EmprestimoService()
    SITUACOES_VALIDAS = {"todos", "em_andamento", "atrasados", "devolvidos"}

    def _situacao_atual(self) -> str:
        situacao = self.request.GET.get("situacao", "todos").strip()
        return situacao if situacao in self.SITUACOES_VALIDAS else "todos"

    def _id_filtro(self, param: str) -> int | None:
        valor = self.request.GET.get(param, "").strip()
        return int(valor) if valor.isdigit() else None

    def get_queryset(self):
        return self.service.listar_historico(
            busca=self.request.GET.get("q", ""),
            equipamento_id=self._id_filtro("equipamento"),
            pessoa_id=self._id_filtro("pessoa"),
            situacao=self._situacao_atual(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["busca"] = self.request.GET.get("q", "").strip()
        context["equipamento_selecionado"] = self._id_filtro("equipamento")
        context["pessoa_selecionada"] = self._id_filtro("pessoa")
        context["situacao"] = self._situacao_atual()
        context["equipamentos_filtro"] = Equipamento.objects.order_by("nome", "codigo")
        context["pessoas_filtro"] = Pessoa.objects.order_by("nome", "identificador")
        context["resumo"] = self.service.resumo_historico()
        context["secao_ativa"] = "historico"
        return context
