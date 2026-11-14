"""Serviços orientados a objetos para regras de cadastro e consulta."""

from django.db.models import Q, QuerySet

from .models import Equipamento, Pessoa


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
