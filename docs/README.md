# Documentação — Comparador de Preços de Supermercados

Sistema web do Projeto Integrador II, disponível em **[comparador-precos-web-9j6z](https://comparador-precos-web-9j6z.onrender.com)**, com interface responsiva, API Django e PostgreSQL no Render.

## Visão geral da arquitetura

- **Frontend:** Vue 3, TypeScript e Vite, compilado e servido pelo backend no mesmo domínio.
- **Backend:** Python 3.11, Django e Django REST Framework, que disponibiliza a API e as rotinas de integração.
- **Persistência:** PostgreSQL do serviço publicado, separado de qualquer banco de desenvolvimento.
- **Implantação:** Dockerfile e `render.yaml`, usando a `main` como branch de publicação.
- **Automação:** CI em `.github/workflows/ci.yml`; coleta diária em `.github/workflows/coleta-diaria.yml`.

O acesso ao sistema publicado **não** exige instalação local. As instruções de `manage.py runserver` e `npm run dev` são apenas para desenvolver e testar em um ambiente próprio.

## Fontes e atualização dos preços

As integrações consultam **Savegnago, Atacadão e Carrefour**. O GitHub Actions agenda a atualização diária às **06h no horário de Brasília (UTC−3)**, autenticando-se com OIDC perante a aplicação no Render. A execução dos coletores ocorre no backend publicado, que já tem conexão com o PostgreSQL de produção.

- A **rotina diária** atualiza preços de **ofertas previamente cadastradas**; não é uma descoberta automática ilimitada de novos produtos.
- Importação, conciliação e busca de produtos equivalentes por EAN são tarefas específicas, distintas do agendamento diário.
- O sistema não deve fabricar valores: mudanças ou observações diárias de preços dependem de consulta às fontes.
- Um comando executado no computador local atua no banco configurado **nesse ambiente**, não no Render.

O modo `CATALOGO_MODO=triangulacao` prioriza produtos com preços nas três redes na apresentação do site; não restringe o catálogo completo retornado pela API `/api/v1/produtos/`.

## Funcionalidades entregues

Pesquisa e listagem de produtos; comparação entre supermercados, com indicação de indisponibilidade; histórico de preços; simulação de lista de compras e total por mercado; imagens e links de ofertas; adaptação da interface a celular e computador.

## Principais endpoints

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| GET | `/api/v1/produtos/` | Busca e catálogo de produtos |
| GET | `/api/v1/supermercados/` | Supermercados ativos |
| GET | `/api/v1/produtos/{id}/comparacao/` | Preços de um produto por rede |
| GET | `/api/v1/produtos/{id}/historico/` | Histórico e filtro opcional por mercado |
| POST | `/api/v1/listas/simular/` | Simulação de lista e totais |
| GET | `/api/v1/configuracao/` | Configuração do modo de catálogo |

## Publicação, testes e manutenção

Os commits chegam à `main` por Pull Request. A CI verifica Django/PostgreSQL, build Vue e Docker. O Render está configurado para implantar a `main` após a aprovação das verificações (`checksPass`). Uma alteração aprovada no GitHub pode não estar publicada ainda; confira o commit em [Render → Deploys](https://dashboard.render.com/web/srv-dbnfnfbrjlhs738meva0).

A atualização de preços pode ser consultada ou iniciada manualmente na aba [GitHub Actions](https://github.com/caiofvserra/comparador-precos/actions).

**Documentação de referência:** [README principal](../README.md) · [Backend](../backend/README.md) · [Frontend](../frontend/README.md). Estes dois últimos incluem instruções **opcionais** de execução local para desenvolvedores.
