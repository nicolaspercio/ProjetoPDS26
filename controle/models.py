"""Modelos orientados a objetos do domínio de equipamentos e pessoas."""

from django.core.exceptions import ValidationError
from django.db import models


def normalizar_chave_unica(valor: str) -> str:
    """Remove espaços extras e padroniza em maiúsculas para evitar duplicidade."""
    return " ".join((valor or "").strip().split()).upper()


class Equipamento(models.Model):
    """Representa um equipamento do laboratório disponível para empréstimo."""

    nome = models.CharField("Nome", max_length=120)
    codigo = models.CharField("Código de identificação", max_length=40, unique=True)
    descricao = models.TextField("Descrição", blank=True)
    disponivel = models.BooleanField("Disponível", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["nome", "codigo"]
        verbose_name = "Equipamento"
        verbose_name_plural = "Equipamentos"

    def __str__(self) -> str:
        return f"{self.nome} ({self.codigo})"

    @staticmethod
    def normalizar_codigo(valor: str) -> str:
        """Padroniza o código de identificação do equipamento."""
        return normalizar_chave_unica(valor)

    def esta_disponivel(self) -> bool:
        """Indica se o equipamento pode ser emprestado no momento."""
        return bool(self.disponivel)

    def situacao_label(self) -> str:
        """Retorna o rótulo textual da situação atual do equipamento."""
        return "Disponível" if self.esta_disponivel() else "Emprestado"

    def clean(self) -> None:
        """Valida campos obrigatórios e unicidade do código de identificação."""
        super().clean()
        self.nome = (self.nome or "").strip()
        self.codigo = self.normalizar_codigo(self.codigo)
        self.descricao = (self.descricao or "").strip()

        if not self.nome:
            raise ValidationError({"nome": "Informe o nome do equipamento."})
        if not self.codigo:
            raise ValidationError(
                {"codigo": "Informe o código de identificação do equipamento."}
            )

        duplicado = Equipamento.objects.filter(codigo__iexact=self.codigo)
        if self.pk:
            duplicado = duplicado.exclude(pk=self.pk)
        if duplicado.exists():
            raise ValidationError(
                {
                    "codigo": (
                        "Já existe um equipamento cadastrado com este código de "
                        "identificação."
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        """Normaliza o código antes de persistir no SQLite."""
        self.nome = (self.nome or "").strip()
        self.codigo = self.normalizar_codigo(self.codigo)
        self.descricao = (self.descricao or "").strip()
        super().save(*args, **kwargs)


class Pessoa(models.Model):
    """Representa uma pessoa autorizada a retirar equipamentos do laboratório."""

    nome = models.CharField("Nome", max_length=120)
    identificador = models.CharField(
        "Matrícula ou identificador", max_length=50, unique=True
    )
    contato = models.CharField("Contato", max_length=120)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["nome", "identificador"]
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"

    def __str__(self) -> str:
        return self.resumo_exibicao()

    @staticmethod
    def normalizar_identificador(valor: str) -> str:
        """Padroniza a matrícula ou identificador da pessoa."""
        return normalizar_chave_unica(valor)

    def resumo_exibicao(self) -> str:
        """Formata nome e identificador para seleção em listas e empréstimos."""
        return f"{self.nome} ({self.identificador})"

    def clean(self) -> None:
        """Valida campos obrigatórios e unicidade do identificador."""
        super().clean()
        self.nome = (self.nome or "").strip()
        self.identificador = self.normalizar_identificador(self.identificador)
        self.contato = (self.contato or "").strip()

        if not self.nome:
            raise ValidationError({"nome": "Informe o nome da pessoa."})
        if not self.identificador:
            raise ValidationError(
                {"identificador": "Informe a matrícula ou identificador."}
            )
        if not self.contato:
            raise ValidationError({"contato": "Informe um contato (e-mail ou telefone)."})

        duplicado = Pessoa.objects.filter(identificador__iexact=self.identificador)
        if self.pk:
            duplicado = duplicado.exclude(pk=self.pk)
        if duplicado.exists():
            raise ValidationError(
                {
                    "identificador": (
                        "Já existe uma pessoa cadastrada com esta matrícula ou "
                        "identificador."
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        """Normaliza o identificador antes de persistir no SQLite."""
        self.nome = (self.nome or "").strip()
        self.identificador = self.normalizar_identificador(self.identificador)
        self.contato = (self.contato or "").strip()
        super().save(*args, **kwargs)
