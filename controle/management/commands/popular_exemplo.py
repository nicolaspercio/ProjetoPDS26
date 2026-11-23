"""Comando para popular dados iniciais de demonstração no banco SQLite."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from controle.models import Emprestimo, Equipamento, Pessoa


class Command(BaseCommand):
    """Insere equipamentos e pessoas de exemplo sem duplicar registros."""

    help = "Popula equipamentos e pessoas iniciais para demonstração do laboratório."

    def handle(self, *args, **options) -> None:
        equipamentos = [
            (
                "Notebook Dell Latitude 5420",
                "NB-001",
                "Intel Core i5, 16GB RAM, carregador incluso.",
                True,
            ),
            (
                "Projetor Epson PowerLite X49",
                "PRJ-001",
                "Acompanha cabo HDMI e controle remoto.",
                True,
            ),
            (
                "Teclado Mecânico Logitech",
                "TEC-002",
                "Layout ABNT2 USB para bancada de testes.",
                False,
            ),
            (
                "Kit Arduino Uno R3",
                "ARD-004",
                "Caixa organizadora com protoboard e jumpers.",
                True,
            ),
        ]
        for nome, codigo, descricao, disponivel in equipamentos:
            Equipamento.objects.get_or_create(
                codigo=Equipamento.normalizar_codigo(codigo),
                defaults={
                    "nome": nome,
                    "descricao": descricao,
                    "disponivel": disponivel,
                },
            )

        pessoas = [
            ("Nicolas Percio", "12211BSI001", "nicolaspercio@ufu.br"),
            ("Mariana Oliveira", "12311BSI014", "mariana.oliveira@ufu.br"),
            ("Lucas Mendes", "12321BSI027", "(34) 99812-3400"),
        ]
        for nome, identificador, contato in pessoas:
            Pessoa.objects.get_or_create(
                identificador=Pessoa.normalizar_identificador(identificador),
                defaults={
                    "nome": nome,
                    "contato": contato,
                },
            )

        teclado = Equipamento.objects.get(codigo="TEC-002")
        mariana = Pessoa.objects.get(identificador="12311BSI014")
        hoje = timezone.localdate()
        if (
            not teclado.esta_disponivel()
            and not Emprestimo.objects.filter(
                equipamento=teclado, data_devolucao__isnull=True
            ).exists()
        ):
            Emprestimo.objects.create(
                equipamento=teclado,
                pessoa=mariana,
                data_retirada=hoje - timedelta(days=10),
                prazo_devolucao=hoje - timedelta(days=3),
            )

        arduino = Equipamento.objects.get(codigo="ARD-004")
        nicolas = Pessoa.objects.get(identificador="12211BSI001")
        if not Emprestimo.objects.filter(equipamento=arduino).exists():
            Emprestimo.objects.create(
                equipamento=arduino,
                pessoa=nicolas,
                data_retirada=hoje - timedelta(days=14),
                prazo_devolucao=hoje - timedelta(days=7),
                data_devolucao=hoje - timedelta(days=8),
            )

        self.stdout.write(self.style.SUCCESS("Dados de exemplo verificados com sucesso."))
