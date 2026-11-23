# Controle de Empréstimos de Equipamentos

Trabalho da disciplina de Processo de Desenvolvimento de Software, do curso de Sistemas de Informação da UFU.

Integrante: Nicolas Percio da Silva.
O trabalho será desenvolvido individualmente.

A proposta é desenvolver um sistema web para controlar os empréstimos de equipamentos de um laboratório de informática. Será possível cadastrar equipamentos e pessoas, registrar empréstimos e devoluções, consultar os materiais disponíveis e acompanhar atrasos e histórico.

As tecnologias previstas são Python com Django para o backend orientado a objetos, HTML e CSS para a interface e SQLite para o banco de dados.

O desenvolvimento seguirá o Scrum com as adaptações da disciplina. As atividades serão acompanhadas no Jira, e o código e a documentação ficarão neste repositório.

## Funcionalidades implementadas (Sprints 2, 3 e 4)

- **US01 — Cadastrar equipamentos:** cadastro com nome, código de identificação (único, normalizado) e descrição.
- **US02 — Cadastrar pessoas:** cadastro com nome, matrícula/identificador (único, normalizado) e contato, disponibilizando as pessoas para seleção.
- **US03 — Consultar equipamentos disponíveis:** listagem com nome, código, descrição e situação (`Disponível` / `Emprestado`), com filtro por situação e busca por nome ou código.
- **US04 — Registrar empréstimo:** seleção de equipamento disponível e pessoa cadastrada, com data de retirada, prazo de devolução e bloqueio de novo empréstimo para item não devolvido.
- **US05 — Registrar devolução:** seleção de empréstimo em aberto, registro da data de devolução, retorno automático do equipamento para `Disponível` e preservação do histórico.
- **US06 — Consultar empréstimos em andamento:** listagem exclusiva dos empréstimos sem devolução, com pesquisa por pessoa ou equipamento.
- **US07 — Identificar empréstimos atrasados:** listagem de empréstimos em aberto cujo prazo de devolução venceu, exibindo responsável, contato, equipamento e dias de atraso, retirando da lista após a devolução.
- **US08 — Consultar histórico de empréstimos:** visualização de empréstimos em andamento, atrasados e devolvidos com datas de retirada, prazo e devolução, além de filtros por equipamento, pessoa e situação.

## Como executar localmente

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py popular_exemplo
python manage.py runserver
```

Para executar os testes automatizados:

```bash
python manage.py test
```
