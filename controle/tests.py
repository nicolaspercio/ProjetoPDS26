"""Testes automatizados das histórias US01 a US08 (Sprints 2, 3 e 4)."""

from datetime import date, timedelta
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Emprestimo, Equipamento, Pessoa
from .services import (
    CadastroPessoasService,
    CatalogoEquipamentosService,
    EmprestimoService,
)


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
            "controle:emprestimo_list",
            "controle:emprestimo_create",
            "controle:devolucao_create",
            "controle:atraso_list",
            "controle:historico_list",
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
        self.assertEqual(Emprestimo.objects.filter(data_devolucao__isnull=True).count(), 1)


class EmprestimoTests(TestCase):
    """Verifica os critérios de aceitação de US04, US05 e US06."""

    def setUp(self) -> None:
        self.equipamento_service = CatalogoEquipamentosService()
        self.pessoa_service = CadastroPessoasService()
        self.emprestimo_service = EmprestimoService()

        self.notebook = self.equipamento_service.cadastrar(
            "Notebook Dell", "NB-001", "16GB RAM"
        )
        self.projetor = self.equipamento_service.cadastrar(
            "Projetor Epson", "PRJ-001", "HDMI"
        )
        self.mariana = self.pessoa_service.cadastrar(
            "Mariana Oliveira", "12311BSI014", "mariana@ufu.br"
        )
        self.lucas = self.pessoa_service.cadastrar(
            "Lucas Mendes", "12321BSI027", "(34) 99812-3400"
        )

    def test_us04_registrar_emprestimo_valido_e_impedir_duplicidade_em_aberto(
        self,
    ) -> None:
        resp = self.client.post(
            reverse("controle:emprestimo_create"),
            data={
                "equipamento": self.notebook.pk,
                "pessoa": self.mariana.pk,
                "data_retirada": "2026-11-20",
                "prazo_devolucao": "2026-11-27",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.notebook.refresh_from_db()
        self.assertFalse(self.notebook.esta_disponivel())
        self.assertEqual(Emprestimo.objects.count(), 1)
        self.assertContains(resp, "Notebook Dell")
        self.assertContains(resp, "Mariana Oliveira")

        # Tentar emprestar novamente o mesmo equipamento em aberto deve falhar
        resp_dup = self.client.post(
            reverse("controle:emprestimo_create"),
            data={
                "equipamento": self.notebook.pk,
                "pessoa": self.lucas.pk,
                "data_retirada": "2026-11-21",
                "prazo_devolucao": "2026-11-28",
            },
        )
        self.assertEqual(resp_dup.status_code, 200)
        self.assertEqual(Emprestimo.objects.count(), 1)
        self.assertContains(resp_dup, "já está emprestado", count=1)

        with self.assertRaises(ValidationError):
            self.emprestimo_service.registrar_emprestimo(
                self.notebook,
                self.lucas,
                date(2026, 11, 21),
                date(2026, 11, 28),
            )

    def test_us04_impedir_prazo_anterior_a_data_de_retirada(self) -> None:
        resp = self.client.post(
            reverse("controle:emprestimo_create"),
            data={
                "equipamento": self.projetor.pk,
                "pessoa": self.mariana.pk,
                "data_retirada": "2026-11-23",
                "prazo_devolucao": "2026-11-20",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Emprestimo.objects.count(), 0)
        self.assertContains(
            resp, "O prazo de devolução não pode ser anterior à data de retirada."
        )

    def test_us05_registrar_devolucao_libera_equipamento_e_preserva_historico(
        self,
    ) -> None:
        emprestimo = self.emprestimo_service.registrar_emprestimo(
            self.notebook,
            self.mariana,
            date(2026, 11, 20),
            date(2026, 11, 27),
        )
        resp = self.client.post(
            reverse("controle:devolucao_create"),
            data={
                "emprestimo": emprestimo.pk,
                "data_devolucao": "2026-11-23",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        emprestimo.refresh_from_db()
        self.notebook.refresh_from_db()

        self.assertEqual(emprestimo.data_devolucao, date(2026, 11, 23))
        self.assertFalse(emprestimo.esta_em_andamento())
        self.assertTrue(self.notebook.esta_disponivel())
        self.assertEqual(Emprestimo.objects.count(), 1)
        self.assertContains(resp, "Devolução de")

        # Após devolução, o equipamento pode ser emprestado novamente
        novo = self.emprestimo_service.registrar_emprestimo(
            self.notebook,
            self.lucas,
            date(2026, 11, 24),
            date(2026, 11, 30),
        )
        self.assertTrue(novo.esta_em_andamento())
        self.assertEqual(Emprestimo.objects.count(), 2)

    def test_us05_impedir_devolucao_anterior_a_retirada(self) -> None:
        emprestimo = self.emprestimo_service.registrar_emprestimo(
            self.projetor,
            self.mariana,
            date(2026, 11, 20),
            date(2026, 11, 27),
        )
        resp = self.client.post(
            reverse("controle:devolucao_create"),
            data={
                "emprestimo": emprestimo.pk,
                "data_devolucao": "2026-11-18",
            },
        )
        self.assertEqual(resp.status_code, 200)
        emprestimo.refresh_from_db()
        self.assertIsNone(emprestimo.data_devolucao)
        self.assertContains(
            resp, "A data de devolução não pode ser anterior à data de retirada."
        )

    def test_us06_consultar_emprestimos_em_andamento_exclui_devolvidos_e_filtra(
        self,
    ) -> None:
        emp_aberto = self.emprestimo_service.registrar_emprestimo(
            self.notebook,
            self.mariana,
            date(2026, 11, 20),
            date(2026, 11, 27),
        )
        emp_devolvido = self.emprestimo_service.registrar_emprestimo(
            self.projetor,
            self.lucas,
            date(2026, 11, 18),
            date(2026, 11, 25),
        )
        self.emprestimo_service.registrar_devolucao(emp_devolvido, date(2026, 11, 21))

        resp = self.client.get(reverse("controle:emprestimo_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Notebook Dell (NB-001)")
        self.assertContains(resp, "Mariana Oliveira")
        self.assertNotContains(resp, "Projetor Epson (PRJ-001)")
        self.assertEqual(resp.context["total_em_andamento"], 1)

        resp_busca_pessoa = self.client.get(
            reverse("controle:emprestimo_list"), {"q": "Mariana"}
        )
        self.assertContains(resp_busca_pessoa, "NB-001")

        resp_busca_codigo = self.client.get(
            reverse("controle:emprestimo_list"), {"q": "NB-001"}
        )
        self.assertContains(resp_busca_codigo, emp_aberto.pessoa.nome)

        resp_vazio = self.client.get(
            reverse("controle:emprestimo_list"), {"q": "Lucas"}
        )
        self.assertContains(resp_vazio, "Nenhum empréstimo em andamento encontrado.")

    def test_us07_identificar_atrasados_prazo_hoje_e_retirar_ao_devolver(self) -> None:
        hoje = timezone.localdate()
        emp_atrasado = self.emprestimo_service.registrar_emprestimo(
            self.notebook,
            self.mariana,
            hoje - timedelta(days=10),
            hoje - timedelta(days=3),
        )
        emp_hoje = self.emprestimo_service.registrar_emprestimo(
            self.projetor,
            self.lucas,
            hoje - timedelta(days=4),
            hoje,
        )

        self.assertTrue(emp_atrasado.esta_atrasado(referencia=hoje))
        self.assertEqual(emp_atrasado.dias_em_atraso(referencia=hoje), 3)
        self.assertFalse(emp_hoje.esta_atrasado(referencia=hoje))
        self.assertEqual(emp_atrasado.situacao_label(referencia=hoje), "Atrasado")
        self.assertEqual(emp_hoje.situacao_label(referencia=hoje), "Em andamento")

        resp = self.client.get(reverse("controle:atraso_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Notebook Dell (NB-001)")
        self.assertContains(resp, "Mariana Oliveira")
        self.assertContains(resp, "3 dias de atraso")
        self.assertNotContains(resp, "Projetor Epson (PRJ-001)")
        self.assertEqual(resp.context["total_atrasados"], 1)

        # Ao devolver o empréstimo atrasado, ele sai imediatamente da lista de atrasados
        self.emprestimo_service.registrar_devolucao(emp_atrasado, hoje)
        resp_pos = self.client.get(reverse("controle:atraso_list"))
        self.assertNotContains(resp_pos, "Notebook Dell (NB-001)")
        self.assertContains(resp_pos, "Nenhum empréstimo em atraso encontrado.")
        self.assertEqual(resp_pos.context["total_atrasados"], 0)

    def test_us08_consultar_historico_completo_com_filtros_por_equipamento_e_pessoa(
        self,
    ) -> None:
        hoje = timezone.localdate()
        emp_devolvido = self.emprestimo_service.registrar_emprestimo(
            self.notebook,
            self.mariana,
            hoje - timedelta(days=12),
            hoje - timedelta(days=5),
        )
        self.emprestimo_service.registrar_devolucao(
            emp_devolvido, hoje - timedelta(days=6)
        )

        self.emprestimo_service.registrar_emprestimo(
            self.projetor,
            self.lucas,
            hoje - timedelta(days=1),
            hoje + timedelta(days=6),
        )

        resp_todos = self.client.get(reverse("controle:historico_list"))
        self.assertEqual(resp_todos.status_code, 200)
        self.assertContains(resp_todos, "Notebook Dell (NB-001)")
        self.assertContains(resp_todos, "Projetor Epson (PRJ-001)")
        self.assertContains(resp_todos, "Devolvido")
        self.assertContains(resp_todos, "Em andamento")
        self.assertContains(resp_todos, (hoje - timedelta(days=6)).strftime("%d/%m/%Y"))

        resp_eq = self.client.get(
            reverse("controle:historico_list"), {"equipamento": self.notebook.pk}
        )
        self.assertEqual(list(resp_eq.context["emprestimos"]), [emp_devolvido])
        self.assertContains(resp_eq, "<td>Notebook Dell (NB-001)</td>", html=False)
        self.assertNotContains(resp_eq, "<td>Projetor Epson (PRJ-001)</td>", html=False)

        resp_pessoa = self.client.get(
            reverse("controle:historico_list"), {"pessoa": self.lucas.pk}
        )
        self.assertContains(resp_pessoa, "<td>Lucas Mendes (12321BSI027)</td>", html=False)
        self.assertNotContains(
            resp_pessoa, "<td>Mariana Oliveira (12311BSI014)</td>", html=False
        )

        resp_dev = self.client.get(
            reverse("controle:historico_list"), {"situacao": "devolvidos"}
        )
        self.assertEqual(list(resp_dev.context["emprestimos"]), [emp_devolvido])
        self.assertContains(resp_dev, "<td>Notebook Dell (NB-001)</td>", html=False)
        self.assertNotContains(resp_dev, "<td>Projetor Epson (PRJ-001)</td>", html=False)
