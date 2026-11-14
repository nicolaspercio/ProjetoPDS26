"""Formulários Django com normalização e validação via modelos."""

from django import forms

from .models import Equipamento, Pessoa


class EquipamentoForm(forms.ModelForm):
    """Formulário de cadastro de equipamentos (US01)."""

    class Meta:
        model = Equipamento
        fields = ["nome", "codigo", "descricao"]
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


class PessoaForm(forms.ModelForm):
    """Formulário de cadastro de pessoas (US02)."""

    class Meta:
        model = Pessoa
        fields = ["nome", "identificador", "contato"]
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
