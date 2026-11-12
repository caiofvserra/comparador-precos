# 🛒 Comparador de Preços de Supermercados

Aplicação **web** do Projeto Integrador II para pesquisar produtos, comparar preços, consultar históricos e estimar o custo de listas de compras nos supermercados **Savegnago, Atacadão e Carrefour**.

**[Acessar a aplicação publicada](https://comparador-precos-web-9j6z.onrender.com)** · **[API pública](https://comparador-precos-web-9j6z.onrender.com/api/v1/)** · **[GitHub Actions](https://github.com/caiofvserra/comparador-precos/actions)**

> **Ambiente de produção:** frontend Vue e API Django publicados juntos no **Render**, com banco **PostgreSQL** e atualização de preços agendada no **GitHub Actions**. Não é necessário instalar Python, PostgreSQL ou Node.js para usar o site. Executar comandos num computador local não atualiza os dados hospedados.

## O que o sistema faz

- Pesquisa e listagem de produtos com imagens quando disponíveis.
- Comparação de preços e indicação de indisponibilidade por supermercado.
- Histórico das observações e mudanças de preços, quando registradas.
- Lista de compras com quantidades, totais e identificação de itens ausentes em cada supermercado.
- Interface responsiva para computadores e celulares.
- Links para as fontes das ofertas e para as redes de supermercados.

Os valores exibidos em produção provêm das integrações implementadas, e **não de preços inventados para a apresentação**. A disponibilidade e a cobertura dependem dos dados efetivamente obtidos em cada fonte.

## Arquitetura em produção

| Componente | Tecnologia / onde funciona |
| --- | --- |
| Interface | Vue 3, TypeScript e Vite; build servido pelo Django no Render |
| API | Python 3.11, Django e Django REST Framework, no mesmo domínio |
| Banco de dados | PostgreSQL associado ao serviço no Render |
| Empacotamento | Dockerfile na raiz do repositório |
| Integração contínua | `.github/workflows/ci.yml`: testes do backend, build do frontend e build Docker |
| Atualização de preços | `.github/workflows/coleta-diaria.yml`: agendamento via GitHub Actions, executado no ambiente publicado |

A definição de infraestrutura está em `render.yaml`. O serviço público utilizado pelo agendamento é **[comparador-precos-web-9j6z](https://comparador-precos-web-9j6z.onrender.com)**.

## Coleta automática de preços

O workflow **Atualização diária de preços (três mercados)** está agendado para **06h (horário de Brasília, UTC−3)**, diariamente, e também aceita execução manual em **[Actions → workflow de coleta](https://github.com/caiofvserra/comparador-precos/actions)**.

1. O GitHub Actions solicita uma atualização autenticada à aplicação publicada, usando identidade OIDC do workflow.
2. O Django no Render executa o comando de atualização das ofertas de Savegnago, Atacadão e Carrefour, com acesso ao PostgreSQL do próprio ambiente.
3. O workflow acompanha o resultado da execução; falhas gerais são registradas e podem fazer a execução falhar.

**Limite importante:** a rotina diária **atualiza ofertas já cadastradas**. Ela não faz automaticamente uma importação ilimitada de novos produtos. Para ampliar o catálogo, existem comandos próprios de importação, conciliação e busca de correspondências por EAN, executados de forma controlada. O CEP utilizado na coleta agendada é `14010000`.

A coleta não gera preços fictícios. As mudanças de preço alimentam o histórico e a rotina pode registrar uma observação diária de preço inalterado, após consulta real à fonte. A disponibilidade da oferta e falhas de cada coletor devem ser conferidas pelos registros de execução.

### Conferir ou executar a coleta

- Abra o workflow `.github/workflows/coleta-diaria.yml` na aba **Actions** e consulte o resultado mais recente.
- Para uma execução sob demanda, selecione **Run workflow** na branch `main`.
- Confira também os logs do serviço correspondente no Render; a execução agendada não depende de manter um computador pessoal ligado.

**Não confundir:** os comandos `python manage.py ...` executados em um banco de desenvolvimento local **não alteram** o PostgreSQL de produção. O antigo agendamento pelo Windows é apenas uma possibilidade local, não o mecanismo de coleta usado pelo site.

## Modos de catálogo e dados

- **Apresentação web:** `CATALOGO_MODO=triangulacao` no Render prioriza na tela inicial produtos com preços nas **três** redes. Trata-se de um critério de exibição, não de uma rotina de coleta.
- **Catálogo completo:** `CATALOGO_MODO=completo` exibe o catálogo sem essa priorização inicial. A API `GET /api/v1/produtos/` sem `q` continua retornando todos os produtos, ordenados por nome.
- **Modo demonstrativo do frontend:** `VITE_DEMO_MODE=true` habilita mocks ilustrativos apenas quando configurado explicitamente. O Dockerfile da produção define `VITE_DEMO_MODE=false`.
- **Coleta pontual de correspondências:** `validar_trios_por_ean` e `expandir_trios` permitem buscar equivalências entre redes. São tarefas de ampliação controlada, **não** parte da atualização diária automática.

Consulte `backend/README.md` para os comandos específicos de coleta e os detalhes dos contratos da API.

## Entrega de novas versões

O fluxo esperado é: **branch → Pull Request → merge na `main` → CI → deploy no Render**. O serviço principal está configurado para deploy automático **após aprovação das verificações** (`checksPass`).

Se um merge não aparecer no site:

1. Confira na aba **Actions** se a CI referente ao **commit da `main`** terminou com sucesso.
2. Confira em **[Render → serviço principal](https://dashboard.render.com/web/srv-dbnfnfbrjlhs738meva0)** → **Events/Deploys** se houve um deploy novo e se o commit corresponde ao merge.
3. Caso não exista deploy novo mesmo com a CI aprovada, revise a integração/autodeploy entre GitHub e Render. **O merge não publica instantaneamente nem comprova, por si só, que o deploy ocorreu.**
4. Após a publicação, recarregue o site; no celular, teste também em uma aba privada para excluir cache antigo.

O serviço e o banco de **produção não são substituídos** por um servidor iniciado localmente. Evite executar coletas de gravação ou migrações em ambientes compartilhados sem verificar o destino do banco.

## Tecnologias e estrutura

```text
comparador-precos/
├── backend/                    # API Django, modelos, comandos de coleta e testes
├── frontend/                   # Vue 3, TypeScript, Vite e interface responsiva
├── docs/                       # documentação técnica
├── .github/workflows/
│   ├── ci.yml                  # testes e builds
│   └── coleta-diaria.yml       # rotina agendada de produção
├── Dockerfile                  # frontend + backend em um serviço web
├── render.yaml                 # definição de infraestrutura Render
└── README.md
```

## Endpoints principais

| Método | Rota | Uso |
| --- | --- | --- |
| GET | `/api/v1/produtos/` | Pesquisa e lista produtos |
| GET | `/api/v1/supermercados/` | Supermercados ativos |
| GET | `/api/v1/produtos/{id}/comparacao/` | Preços por supermercado |
| GET | `/api/v1/produtos/{id}/historico/` | Histórico por produto |
| POST | `/api/v1/listas/simular/` | Estimativa da lista de compras |
| GET | `/api/v1/configuracao/` | Modo de apresentação do catálogo |

## Desenvolvimento local (opcional)

Para **desenvolver ou testar** o código, consulte **[backend/README.md](backend/README.md)** e **[frontend/README.md](frontend/README.md)**. Eles explicam como iniciar PostgreSQL, Django e Vite num ambiente separado. Os comandos locais não são passos necessários para quem acessa o site publicado.

Documentação complementar: **[docs/README.md](docs/README.md)**. Nunca versione `.env`, tokens, senhas ou credenciais de produção.

---

Projeto Integrador II — Engenharia de Computação · UNIVESP.
