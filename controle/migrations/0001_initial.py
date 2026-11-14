"""Migração inicial dos modelos Equipamento e Pessoa."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Cria as tabelas controle_equipamento e controle_pessoa."""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Equipamento",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nome", models.CharField(max_length=120, verbose_name="Nome")),
                (
                    "codigo",
                    models.CharField(
                        max_length=40,
                        unique=True,
                        verbose_name="Código de identificação",
                    ),
                ),
                ("descricao", models.TextField(blank=True, verbose_name="Descrição")),
                (
                    "disponivel",
                    models.BooleanField(default=True, verbose_name="Disponível"),
                ),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
            ],
            options={
                "verbose_name": "Equipamento",
                "verbose_name_plural": "Equipamentos",
                "ordering": ["nome", "codigo"],
            },
        ),
        migrations.CreateModel(
            name="Pessoa",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nome", models.CharField(max_length=120, verbose_name="Nome")),
                (
                    "identificador",
                    models.CharField(
                        max_length=50,
                        unique=True,
                        verbose_name="Matrícula ou identificador",
                    ),
                ),
                ("contato", models.CharField(max_length=120, verbose_name="Contato")),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
            ],
            options={
                "verbose_name": "Pessoa",
                "verbose_name_plural": "Pessoas",
                "ordering": ["nome", "identificador"],
            },
        ),
    ]
