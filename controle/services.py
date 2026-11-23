"""Serviços orientados a objetos para regras de cadastro, empréstimo e consulta."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from .models import Emprestimo, Equipamento, Pessoa


class CatalogoEquipamentosService:
    """Centraliza consultas, filtros e cadastro de equipamentos (US01 e US03)."""

    def listar(self, busca: str = "", situacao: str = "todos") -> QuerySet[Equipamento]:
        """Retorna equipamentos filtrados por nome/código e situação."""
        qs = Equipamento.objects.all()
        termo = (busca or "").strip()
        if termo:
            qs = qs.filter(Q(nome__icontains=termo) | Q(codigo__icontains=termo))

        if situacao == "disponiveis":
            qs = qs.filter(disponivel=True)
        elif situacao == "emprestados":
            qs = qs.filter(disponivel=False)

        return qs

    def resumo_disponibilidade(self) -> dict[str, int]:
        """Calcula os totais gerais, disponíveis e emprestados do laboratório."""
        total = Equipamento.objects.count()
        disponiveis = Equipamento.objects.filter(disponivel=True).count()
        return {
            "total": total,
            "disponiveis": disponiveis,
            "emprestados": total - disponiveis,
        }

    def cadastrar(
        self, nome: str, codigo: str, descricao: str = "", disponivel: bool = True
    ) -> Equipamento:
        """Valida e persiste um novo equipamento no catálogo."""
        equipamento = Equipamento(
            nome=nome,
            codigo=codigo,
            descricao=descricao,
            disponivel=disponivel,
        )
        equipamento.full_clean()
        equipamento.save()
        return equipamento


class CadastroPessoasService:
    """Centraliza cadastro e listagem de pessoas autorizadas (US02)."""

    def listar(self, busca: str = "") -> QuerySet[Pessoa]:
        """Retorna pessoas filtradas por nome, identificador ou contato."""
        qs = Pessoa.objects.all()
        termo = (busca or "").strip()
        if termo:
            qs = qs.filter(
                Q(nome__icontains=termo)
                | Q(identificador__icontains=termo)
                | Q(contato__icontains=termo)
            )
        return qs

    def listar_para_selecao(self) -> QuerySet[Pessoa]:
        """Disponibiliza as pessoas cadastradas ordenadas para seleção futura."""
        return Pessoa.objects.order_by("nome", "identificador")

    def contar(self) -> int:
        """Retorna a quantidade total de pessoas cadastradas."""
        return Pessoa.objects.count()

    def cadastrar(self, nome: str, identificador: str, contato: str) -> Pessoa:
        """Valida e persiste uma nova pessoa autorizada."""
        pessoa = Pessoa(
            nome=nome,
            identificador=identificador,
            contato=contato,
        )
        pessoa.full_clean()
        pessoa.save()
        return pessoa


class EmprestimoService:
    """Centraliza registro de empréstimos, devoluções e consultas (US04, US05, US06)."""

    def listar_em_andamento(self, busca: str = "") -> QuerySet[Emprestimo]:
        """Retorna apenas empréstimos sem data de devolução, com pesquisa opcional."""
        qs = Emprestimo.objects.select_related("equipamento", "pessoa").filter(
            data_devolucao__isnull=True
        )
        termo = (busca or "").strip()
        if termo:
            qs = qs.filter(
                Q(equipamento__nome__icontains=termo)
                | Q(equipamento__codigo__icontains=termo)
                | Q(pessoa__nome__icontains=termo)
                | Q(pessoa__identificador__icontains=termo)
            )
        return qs

    def contar_em_andamento(self) -> int:
        """Retorna a quantidade de empréstimos em aberto."""
        return Emprestimo.objects.filter(data_devolucao__isnull=True).count()

    @transaction.atomic
    def registrar_emprestimo(
        self,
        equipamento: Equipamento,
        pessoa: Pessoa,
        data_retirada: date,
        prazo_devolucao: date,
    ) -> Emprestimo:
        """Valida disponibilidade e registra novo empréstimo atualizando o equipamento."""
        equipamento_atual = Equipamento.objects.select_for_update().get(pk=equipamento.pk)
        pessoa_atual = Pessoa.objects.get(pk=pessoa.pk)

        emprestimo = Emprestimo(
            equipamento=equipamento_atual,
            pessoa=pessoa_atual,
            data_retirada=data_retirada,
            prazo_devolucao=prazo_devolucao,
        )
        emprestimo.full_clean()
        emprestimo.save()

        equipamento_atual.disponivel = False
        equipamento_atual.save(update_fields=["disponivel"])
        return emprestimo

    @transaction.atomic
    def registrar_devolucao(
        self,
        emprestimo: Emprestimo | int,
        data_devolucao: date | None = None,
    ) -> Emprestimo:
        """Registra a devolução de um empréstimo em aberto e libera o equipamento."""
        emprestimo_id = emprestimo.pk if isinstance(emprestimo, Emprestimo) else emprestimo
        registro = (
            Emprestimo.objects.select_related("equipamento", "pessoa")
            .select_for_update()
            .get(pk=emprestimo_id)
        )

        if not registro.esta_em_andamento():
            raise ValidationError(
                {"emprestimo": "Este empréstimo já teve devolução registrada."}
            )

        registro.data_devolucao = data_devolucao or timezone.localdate()
        registro.full_clean()
        registro.save(update_fields=["data_devolucao"])

        equipamento = Equipamento.objects.select_for_update().get(
            pk=registro.equipamento_id
        )
        equipamento.disponivel = True
        equipamento.save(update_fields=["disponivel"])
        return registro
