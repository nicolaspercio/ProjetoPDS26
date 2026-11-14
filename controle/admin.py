"""Registro dos modelos no painel administrativo do Django."""

from django.contrib import admin

from .models import Equipamento, Pessoa


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo", "disponivel", "criado_em")
    list_filter = ("disponivel",)
    search_fields = ("nome", "codigo")


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ("nome", "identificador", "contato", "criado_em")
    search_fields = ("nome", "identificador", "contato")
