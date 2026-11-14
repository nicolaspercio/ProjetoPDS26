"""Configuração da aplicação controle."""

from django.apps import AppConfig


class ControleConfig(AppConfig):
    """Define metadados do aplicativo de controle de empréstimos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "controle"
    verbose_name = "Controle de Empréstimos"
