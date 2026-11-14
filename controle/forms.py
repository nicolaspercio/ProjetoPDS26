"""Formulários Django com normalização e validação via modelos."""

from django import forms

from .models import Equipamento, Pessoa


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
