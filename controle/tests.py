"""Testes automatizados das histórias US01, US02 e US03 (Sprint 2)."""

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Equipamento, Pessoa
from .services import CadastroPessoasService, CatalogoEquipamentosService


class EquipamentoTests(TestCase):
    """Verifica os critérios de aceitação de US01 e US03."""

    def setUp(self) -> None:
        self.service = CatalogoEquipamentosService()

    def test_us01_cadastrar_equipamento_valido_e_exibir_na_consulta(self) -> None:
        resp = self.client.post(
            reverse("controle:equipamento_create"),
            data={
                "nome": "Notebook Lenovo ThinkPad",
                "codigo": "nb-010",
                "descricao": "i7, 16GB RAM",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Equipamento.objects.filter(codigo="NB-010").exists())
        self.assertContains(resp, "Notebook Lenovo ThinkPad")
        self.assertContains(resp, "NB-010")
        self.assertContains(resp, "Disponível")

    def test_us01_impedir_codigo_duplicado_mesmo_com_caixa_diferente(self) -> None:
        self.service.cadastrar("Projetor Epson", "PRJ-001", "Sala 1B")

        resp = self.client.post(
            reverse("controle:equipamento_create"),
            data={
                "nome": "Outro Projetor",
                "codigo": "prj-001",
                "descricao": "Tentativa duplicada",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Equipamento.objects.count(), 1)
        self.assertContains(resp, "Já existe um equipamento cadastrado com este código")
        self.assertNotContains(resp, "Informe o código de identificação")

        with self.assertRaises(ValidationError):
            self.service.cadastrar("Outro Projetor", "PRJ-001", "Duplicado")

    def test_us03_diferenciar_disponiveis_emprestados_e_filtrar_por_nome_ou_codigo(
        self,
    ) -> None:
        self.service.cadastrar("Notebook Dell", "NB-001", "Disponível", disponivel=True)
        self.service.cadastrar("Teclado USB", "TEC-002", "Em uso", disponivel=False)

        resp_todos = self.client.get(reverse("controle:equipamento_list"))
        self.assertContains(resp_todos, "Disponível")
        self.assertContains(resp_todos, "Emprestado")

        resp_disp = self.client.get(
            reverse("controle:equipamento_list"), {"situacao": "disponiveis"}
        )
        self.assertContains(resp_disp, "Notebook Dell")
        self.assertNotContains(resp_disp, "Teclado USB")

        resp_emp = self.client.get(
            reverse("controle:equipamento_list"), {"situacao": "emprestados"}
        )
        self.assertContains(resp_emp, "Teclado USB")
        self.assertNotContains(resp_emp, "Notebook Dell")

        resp_nome = self.client.get(reverse("controle:equipamento_list"), {"q": "Dell"})
        self.assertContains(resp_nome, "NB-001")
        self.assertNotContains(resp_nome, "TEC-002")

        resp_codigo = self.client.get(
            reverse("controle:equipamento_list"), {"q": "TEC-002"}
        )
        self.assertContains(resp_codigo, "Teclado USB")
        self.assertNotContains(resp_codigo, "Notebook Dell")


class PessoaTests(TestCase):
    """Verifica os critérios de aceitação de US02."""

    def setUp(self) -> None:
        self.service = CadastroPessoasService()

    def test_us02_cadastrar_pessoa_valida_e_disponibilizar_para_selecao(self) -> None:
        resp = self.client.post(
            reverse("controle:pessoa_create"),
            data={
                "nome": "Ana Clara",
                "identificador": "12311bsi099",
                "contato": "ana.clara@ufu.br",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        pessoa = Pessoa.objects.get(identificador="12311BSI099")
        self.assertIn(pessoa, self.service.listar_para_selecao())
        self.assertContains(resp, "Ana Clara (12311BSI099)")

    def test_us02_impedir_identificador_duplicado(self) -> None:
        self.service.cadastrar("Carlos Silva", "MAT-100", "carlos@ufu.br")

        resp = self.client.post(
            reverse("controle:pessoa_create"),
            data={
                "nome": "Carlos Outro",
                "identificador": "mat-100",
                "contato": "outro@ufu.br",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Pessoa.objects.count(), 1)
        self.assertContains(resp, "Já existe uma pessoa cadastrada com esta matrícula")
        self.assertNotContains(resp, "Informe a matrícula ou identificador")

        with self.assertRaises(ValidationError):
            self.service.cadastrar("Carlos Outro", "MAT-100", "outro@ufu.br")
