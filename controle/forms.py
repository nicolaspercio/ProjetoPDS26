"""Formulários Django com normalização e validação via modelos."""

from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import Emprestimo, Equipamento, Pessoa


class SemErrosDuplicadosMixin:
    """Evita duplicar erros de modelo em campos que já falharam na validação do form."""

    def _post_clean(self) -> None:
        erros_previos = set(self._errors.keys()) if self._errors else set()
        super()._post_clean()
        for campo in erros_previos:
            if campo in self._errors and len(self._errors[campo]) > 1:
                self._errors[campo] = self.error_class([self._errors[campo][0]])


class EquipamentoForm(SemErrosDuplicadosMixin, forms.ModelForm):
    """Formulário de cadastro de equipamentos (US01)."""

    class Meta:
        model = Equipamento
        fields = ["nome", "codigo", "descricao"]
        error_messages = {
            "nome": {"required": "Informe o nome do equipamento."},
            "codigo": {"required": "Informe o código de identificação do equipamento."},
        }
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: Notebook Dell Latitude 5420",
                    "autocomplete": "off",
                }
            ),
            "codigo": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: NB-001",
                    "autocomplete": "off",
                }
            ),
            "descricao": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Configuração, acessórios ou observações do item...",
                }
            ),
        }

    def clean_codigo(self) -> str:
        """Normaliza o código antes da validação de domínio no modelo."""
        return Equipamento.normalizar_codigo(self.cleaned_data.get("codigo", ""))


class PessoaForm(SemErrosDuplicadosMixin, forms.ModelForm):
    """Formulário de cadastro de pessoas (US02)."""

    class Meta:
        model = Pessoa
        fields = ["nome", "identificador", "contato"]
        error_messages = {
            "nome": {"required": "Informe o nome da pessoa."},
            "identificador": {"required": "Informe a matrícula ou identificador."},
            "contato": {"required": "Informe um contato (e-mail ou telefone)."},
        }
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: Mariana Souza",
                    "autocomplete": "off",
                }
            ),
            "identificador": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: 12311BSI001",
                    "autocomplete": "off",
                }
            ),
            "contato": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: mariana@ufu.br ou (34) 99999-0000",
                    "autocomplete": "off",
                }
            ),
        }

    def clean_identificador(self) -> str:
        """Normaliza o identificador antes da validação de domínio no modelo."""
        return Pessoa.normalizar_identificador(
            self.cleaned_data.get("identificador", "")
        )


class EquipamentoEmprestimoChoiceField(forms.ModelChoiceField):
    """Exibe equipamento com código e situação atual na seleção de empréstimo."""

    def label_from_instance(self, obj: Equipamento) -> str:
        return f"{obj.nome} ({obj.codigo}) — {obj.situacao_label()}"


class EmprestimoAbertoChoiceField(forms.ModelChoiceField):
    """Exibe empréstimo em aberto com equipamento, pessoa e prazo."""

    def label_from_instance(self, obj: Emprestimo) -> str:
        return (
            f"{obj.equipamento.nome} ({obj.equipamento.codigo}) — "
            f"{obj.pessoa.nome} (prazo {obj.prazo_devolucao:%d/%m/%Y})"
        )


class EmprestimoForm(SemErrosDuplicadosMixin, forms.ModelForm):
    """Formulário de registro de empréstimo (US04)."""

    equipamento = EquipamentoEmprestimoChoiceField(
        queryset=Equipamento.objects.order_by("nome", "codigo"),
        empty_label="Selecione um equipamento...",
        label="Equipamento",
        error_messages={"required": "Selecione o equipamento."},
    )
    pessoa = forms.ModelChoiceField(
        queryset=Pessoa.objects.order_by("nome", "identificador"),
        empty_label="Selecione uma pessoa...",
        label="Pessoa responsável",
        error_messages={"required": "Selecione a pessoa responsável."},
    )

    class Meta:
        model = Emprestimo
        fields = ["equipamento", "pessoa", "data_retirada", "prazo_devolucao"]
        error_messages = {
            "data_retirada": {"required": "Informe a data de retirada."},
            "prazo_devolucao": {"required": "Informe o prazo de devolução."},
        }
        widgets = {
            "data_retirada": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date"}
            ),
            "prazo_devolucao": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            hoje = timezone.localdate()
            self.initial.setdefault("data_retirada", hoje)
            self.initial.setdefault("prazo_devolucao", hoje + timedelta(days=7))


class DevolucaoForm(forms.Form):
    """Formulário de registro de devolução de empréstimo em aberto (US05)."""

    emprestimo = EmprestimoAbertoChoiceField(
        queryset=Emprestimo.objects.none(),
        empty_label="Selecione um empréstimo em aberto...",
        label="Empréstimo em aberto",
        error_messages={"required": "Selecione o empréstimo a ser devolvido."},
    )
    data_devolucao = forms.DateField(
        label="Data da devolução",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        error_messages={"required": "Informe a data da devolução."},
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["emprestimo"].queryset = (
            Emprestimo.objects.select_related("equipamento", "pessoa")
            .filter(data_devolucao__isnull=True)
            .order_by("prazo_devolucao", "data_retirada")
        )
        if not self.is_bound:
            self.initial.setdefault("data_devolucao", timezone.localdate())
