"""Modelos orientados a objetos do domínio de equipamentos, pessoas e empréstimos."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


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

        erros: dict[str, str] = {}
        if not self.nome:
            erros["nome"] = "Informe o nome do equipamento."
        if not self.codigo:
            erros["codigo"] = "Informe o código de identificação do equipamento."
        else:
            duplicado = Equipamento.objects.filter(codigo__iexact=self.codigo)
            if self.pk:
                duplicado = duplicado.exclude(pk=self.pk)
            if duplicado.exists():
                erros["codigo"] = (
                    "Já existe um equipamento cadastrado com este código de "
                    "identificação."
                )

        if erros:
            raise ValidationError(erros)

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

        erros: dict[str, str] = {}
        if not self.nome:
            erros["nome"] = "Informe o nome da pessoa."
        if not self.identificador:
            erros["identificador"] = "Informe a matrícula ou identificador."
        else:
            duplicado = Pessoa.objects.filter(identificador__iexact=self.identificador)
            if self.pk:
                duplicado = duplicado.exclude(pk=self.pk)
            if duplicado.exists():
                erros["identificador"] = (
                    "Já existe uma pessoa cadastrada com esta matrícula ou "
                    "identificador."
                )
        if not self.contato:
            erros["contato"] = "Informe um contato (e-mail ou telefone)."

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs) -> None:
        """Normaliza o identificador antes de persistir no SQLite."""
        self.nome = (self.nome or "").strip()
        self.identificador = self.normalizar_identificador(self.identificador)
        self.contato = (self.contato or "").strip()
        super().save(*args, **kwargs)


class Emprestimo(models.Model):
    """Representa o empréstimo de um equipamento para uma pessoa autorizada."""

    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="emprestimos",
        verbose_name="Equipamento",
    )
    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.PROTECT,
        related_name="emprestimos",
        verbose_name="Pessoa",
    )
    data_retirada = models.DateField("Data de retirada")
    prazo_devolucao = models.DateField("Prazo de devolução")
    data_devolucao = models.DateField("Data de devolução", null=True, blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["-data_retirada", "-criado_em"]
        verbose_name = "Empréstimo"
        verbose_name_plural = "Empréstimos"
        constraints = [
            models.UniqueConstraint(
                fields=["equipamento"],
                condition=Q(data_devolucao__isnull=True),
                name="uniq_emprestimo_aberto_por_equipamento",
            )
        ]

    def __str__(self) -> str:
        return f"{self.equipamento} -> {self.pessoa}"

    def esta_em_andamento(self) -> bool:
        """Indica se o empréstimo ainda não foi devolvido."""
        return self.data_devolucao is None

    def esta_atrasado(self, referencia: date | None = None) -> bool:
        """Indica se o empréstimo segue em aberto após o prazo de devolução."""
        hoje = referencia or timezone.localdate()
        return self.esta_em_andamento() and self.prazo_devolucao < hoje

    def dias_em_atraso(self, referencia: date | None = None) -> int:
        """Calcula quantos dias se passaram desde o vencimento do prazo."""
        if not self.esta_atrasado(referencia=referencia):
            return 0
        hoje = referencia or timezone.localdate()
        return (hoje - self.prazo_devolucao).days

    def situacao_label(self, referencia: date | None = None) -> str:
        """Retorna o rótulo textual da situação atual do empréstimo."""
        if not self.esta_em_andamento():
            return "Devolvido"
        if self.esta_atrasado(referencia=referencia):
            return "Atrasado"
        return "Em andamento"

    def clean(self) -> None:
        """Valida datas e impede novo empréstimo de equipamento não devolvido."""
        super().clean()
        erros: dict[str, str] = {}

        if (
            self.data_retirada is not None
            and self.prazo_devolucao is not None
            and self.prazo_devolucao < self.data_retirada
        ):
            erros["prazo_devolucao"] = (
                "O prazo de devolução não pode ser anterior à data de retirada."
            )

        if (
            self.data_devolucao is not None
            and self.data_retirada is not None
            and self.data_devolucao < self.data_retirada
        ):
            erros["data_devolucao"] = (
                "A data de devolução não pode ser anterior à data de retirada."
            )

        if self.esta_em_andamento() and self.equipamento_id:
            aberto_existente = Emprestimo.objects.filter(
                equipamento_id=self.equipamento_id,
                data_devolucao__isnull=True,
            )
            if self.pk:
                aberto_existente = aberto_existente.exclude(pk=self.pk)

            if aberto_existente.exists() or (
                not self.pk and not self.equipamento.esta_disponivel()
            ):
                erros["equipamento"] = (
                    "Este equipamento já está emprestado e não pode ser retirado "
                    "antes da devolução."
                )

        if erros:
            raise ValidationError(erros)
