"""Testes automatizados das histórias US01, US02 e US03 (Sprint 2)."""

from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
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
        equipamento = Equipamento.objects.get(codigo="NB-010")
        self.assertTrue(equipamento.esta_disponivel())
        self.assertEqual(equipamento.situacao_label(), "Disponível")
        self.assertEqual(str(equipamento), "Notebook Lenovo ThinkPad (NB-010)")
        self.assertContains(resp, "Notebook Lenovo ThinkPad")
        self.assertContains(resp, "NB-010")
        self.assertContains(resp, "Disponível")

    def test_us01_cadastrar_equipamento_sem_descricao_e_rejeitar_campos_vazios(
        self,
    ) -> None:
        resp_vazio = self.client.post(
            reverse("controle:equipamento_create"),
            data={"nome": "   ", "codigo": "   ", "descricao": ""},
        )
        self.assertEqual(resp_vazio.status_code, 200)
        self.assertEqual(Equipamento.objects.count(), 0)
        self.assertContains(resp_vazio, "Corrija os campos abaixo")
        self.assertContains(resp_vazio, "Informe o nome do equipamento.", count=1)
        self.assertContains(
            resp_vazio, "Informe o código de identificação do equipamento.", count=1
        )
        self.assertNotContains(resp_vazio, "Este campo é obrigatório.")

        with self.assertRaises(ValidationError) as ctx:
            self.service.cadastrar("   ", "   ")
        self.assertEqual(set(ctx.exception.message_dict.keys()), {"nome", "codigo"})

        resp_ok = self.client.post(
            reverse("controle:equipamento_create"),
            data={"nome": "Mouse USB", "codigo": "  ms  001  ", "descricao": ""},
            follow=True,
        )
        self.assertEqual(resp_ok.status_code, 200)
        self.assertTrue(Equipamento.objects.filter(codigo="MS 001").exists())
        self.assertContains(resp_ok, "Mouse USB")

    def test_us01_impedir_codigo_duplicado_mesmo_com_caixa_ou_espacos_diferentes(
        self,
    ) -> None:
        self.service.cadastrar("Projetor Epson", "PRJ-001", "Sala 1B")

        resp = self.client.post(
            reverse("controle:equipamento_create"),
            data={
                "nome": "Outro Projetor",
                "codigo": "  prj-001 ",
                "descricao": "Tentativa duplicada",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Equipamento.objects.count(), 1)
        self.assertContains(
            resp, "Já existe um equipamento cadastrado com este código", count=1
        )
        self.assertNotContains(resp, "Informe o código de identificação")

        resp_misto = self.client.post(
            reverse("controle:equipamento_create"),
            data={"nome": "", "codigo": "prj-001", "descricao": ""},
        )
        self.assertContains(resp_misto, "Informe o nome do equipamento.", count=1)
        self.assertContains(
            resp_misto, "Já existe um equipamento cadastrado com este código", count=1
        )

        with self.assertRaises(ValidationError):
            self.service.cadastrar("Outro Projetor", "PRJ-001", "Duplicado")

    def test_us03_diferenciar_disponiveis_emprestados_e_filtrar_por_nome_ou_codigo(
        self,
    ) -> None:
        self.service.cadastrar("Notebook Dell", "NB-001", "Disponível", disponivel=True)
        self.service.cadastrar("Teclado USB", "TEC-002", "Em uso", disponivel=False)

        resp_todos = self.client.get(reverse("controle:equipamento_list"))
        self.assertEqual(resp_todos.status_code, 200)
        self.assertContains(resp_todos, "Disponível")
        self.assertContains(resp_todos, "Emprestado")
        self.assertContains(resp_todos, "Todos (2)")
        self.assertContains(resp_todos, "Disponíveis (1)")
        self.assertContains(resp_todos, "Emprestados (1)")

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

        resp_combinado = self.client.get(
            reverse("controle:equipamento_list"),
            {"q": "Notebook", "situacao": "emprestados"},
        )
        self.assertContains(resp_combinado, "Nenhum equipamento encontrado.")

        resp_invalido = self.client.get(
            reverse("controle:equipamento_list"), {"situacao": "desconhecida"}
        )
        self.assertEqual(resp_invalido.context["situacao"], "todos")
        self.assertContains(resp_invalido, "Notebook Dell")
        self.assertContains(resp_invalido, "Teclado USB")


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
        self.assertEqual(str(pessoa), "Ana Clara (12311BSI099)")
        self.assertIn(pessoa, self.service.listar_para_selecao())
        self.assertContains(resp, "Ana Clara (12311BSI099)")

    def test_us02_impedir_identificador_duplicado_e_campos_vazios(self) -> None:
        resp_vazio = self.client.post(
            reverse("controle:pessoa_create"),
            data={"nome": " ", "identificador": " ", "contato": " "},
        )
        self.assertEqual(resp_vazio.status_code, 200)
        self.assertEqual(Pessoa.objects.count(), 0)
        self.assertContains(resp_vazio, "Corrija os campos abaixo")
        self.assertContains(resp_vazio, "Informe o nome da pessoa.", count=1)
        self.assertContains(resp_vazio, "Informe a matrícula ou identificador.", count=1)
        self.assertContains(
            resp_vazio, "Informe um contato (e-mail ou telefone).", count=1
        )
        self.assertNotContains(resp_vazio, "Este campo é obrigatório.")

        with self.assertRaises(ValidationError) as ctx:
            self.service.cadastrar(" ", " ", " ")
        self.assertEqual(
            set(ctx.exception.message_dict.keys()),
            {"nome", "identificador", "contato"},
        )

        self.service.cadastrar("Carlos Silva", "MAT-100", "carlos@ufu.br")
        self.assertEqual(self.service.contar(), 1)

        resp = self.client.post(
            reverse("controle:pessoa_create"),
            data={
                "nome": "Carlos Outro",
                "identificador": "  mat-100 ",
                "contato": "outro@ufu.br",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Pessoa.objects.count(), 1)
        self.assertContains(
            resp, "Já existe uma pessoa cadastrada com esta matrícula", count=1
        )
        self.assertNotContains(resp, "Informe a matrícula ou identificador")

        with self.assertRaises(ValidationError):
            self.service.cadastrar("Carlos Outro", "MAT-100", "outro@ufu.br")

    def test_us02_pesquisar_pessoas_e_manter_selecao_disponivel(self) -> None:
        self.service.cadastrar("Mariana Oliveira", "12311BSI014", "mariana@ufu.br")
        self.service.cadastrar("Lucas Mendes", "12321BSI027", "(34) 99812-3400")

        resp_busca = self.client.get(reverse("controle:pessoa_list"), {"q": "Mariana"})
        self.assertEqual(resp_busca.status_code, 200)
        self.assertContains(resp_busca, "12311BSI014")
        self.assertNotContains(resp_busca, "<td>Lucas Mendes</td>", html=False)
        self.assertContains(resp_busca, "Lucas Mendes (12321BSI027)")

        resp_sem_resultado = self.client.get(
            reverse("controle:pessoa_list"), {"q": "inexistente"}
        )
        self.assertContains(resp_sem_resultado, "Nenhuma pessoa encontrada.")
        self.assertContains(resp_sem_resultado, "Mariana Oliveira (12311BSI014)")


class NavegacaoEExemploTests(TestCase):
    """Garante carregamento das telas principais e idempotência de popular_exemplo."""

    def test_telas_principais_respondem_com_sucesso(self) -> None:
        rotas = [
            "controle:equipamento_list",
            "controle:equipamento_create",
            "controle:pessoa_list",
            "controle:pessoa_create",
        ]
        for rota in rotas:
            with self.subTest(rota=rota):
                resp = self.client.get(reverse(rota))
                self.assertEqual(resp.status_code, 200)

    def test_comando_popular_exemplo_e_idempotente(self) -> None:
        out = StringIO()
        call_command("popular_exemplo", stdout=out)
        call_command("popular_exemplo", stdout=out)

        self.assertEqual(Equipamento.objects.count(), 4)
        self.assertEqual(Pessoa.objects.count(), 3)
        self.assertEqual(Equipamento.objects.filter(disponivel=True).count(), 3)
        self.assertEqual(Equipamento.objects.filter(disponivel=False).count(), 1)
