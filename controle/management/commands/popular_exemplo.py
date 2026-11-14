"""Comando para popular dados iniciais de demonstração no banco SQLite."""

from django.core.management.base import BaseCommand

from controle.models import Equipamento, Pessoa


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
                codigo=codigo,
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
                identificador=identificador,
                defaults={
                    "nome": nome,
                    "contato": contato,
                },
            )

        self.stdout.write(self.style.SUCCESS("Dados de exemplo verificados com sucesso."))
