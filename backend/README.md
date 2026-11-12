# Backend – Comparador de Preços de Supermercados

API REST em Django + Django REST Framework para o MVP do Projeto Integrador II.
Segue a *Especificação Técnica do MVP v2* (contrato do grupo).

## Aplicação publicada e coleta automática

A aplicação está disponível em **[https://comparador-precos-web-9j6z.onrender.com](https://comparador-precos-web-9j6z.onrender.com)**. O backend Django e o frontend Vue são executados juntos no Render, com banco PostgreSQL do ambiente publicado. O serviço é construído pelo `Dockerfile`; **não é necessário executar `manage.py runserver` para usar o site**.

A coleta diária das três redes é acionada pelo workflow `.github/workflows/coleta-diaria.yml` às **06h (horário de Brasília)**, com autenticação OIDC GitHub → Render. O comando é executado no backend publicado e utiliza o banco de produção, sem enviar credenciais PostgreSQL ao Actions. A coleta agendada **atualiza ofertas previamente cadastradas**, não importa automaticamente um catálogo ilimitado.

Para acompanhar a coleta, consulte [GitHub Actions](https://github.com/caiofvserra/comparador-precos/actions) e os logs do serviço no Render. A CI em `.github/workflows/ci.yml` verifica testes, frontend e Docker, e o deploy da `main` depende de verificações aprovadas.

**Atenção:** usar os comandos abaixo em seu computador utiliza o banco definido no `.env` local; **isso não atualiza a base publicada**. Não execute comandos de gravação em ambiente compartilhado sem verificar a conexão.

## Desenvolvimento local (opcional)

Requisitos: Python 3.11+ e PostgreSQL.

1. Crie o banco e o usuário no PostgreSQL:

   ```sql
   CREATE USER comparador WITH PASSWORD 'comparador' CREATEDB;
   CREATE DATABASE comparador OWNER comparador;
   ```

   O `CREATEDB` é necessário porque o `python manage.py test` cria um banco
   temporário (`test_comparador`) para rodar os testes.

2. Crie o ambiente virtual e instale as dependências:

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copie o `.env.example` para `.env` e ajuste os valores (o `.env` não vai para o Git):

   ```bash
   cp .env.example .env           # Windows: copy .env.example .env
   ```

4. Crie as tabelas do ambiente local:

   ```bash
   python manage.py migrate
   ```

   **Apenas para experimentos com dados ilustrativos no banco local**, pode-se carregar a fixture `python manage.py loaddata dados_exemplo`. Ela não deve substituir a coleta real nem ser carregada no banco de produção.

5. (Opcional) crie um usuário para o Django Admin em `http://localhost:8000/admin/`:

   ```bash
   python manage.py createsuperuser
   ```

6. Suba o servidor:

   ```bash
   python manage.py runserver
   ```

   A API fica em `http://localhost:8000/api/v1/`.

## Testes

```bash
python manage.py test
```

Os testes ficam em `tests/` e cobrem os casos funcionais do backend, incluindo CT-01 a CT-08 do plano de testes. O CT-09 (uso em celular) é validado no frontend por teste visual/responsivo.

## Estrutura

```
backend/
├── config/       # settings, urls
├── catalogo/     # Supermercado, Categoria, Produto + busca e lista de supermercados
├── precos/       # OfertaFonte, Preco + comparação e histórico
├── simulacao/    # cálculo da lista de compras
├── coleta/       # integração com Savegnago, Atacadão e Carrefour
└── tests/        # testes da API
```

## Endpoints

| Método | Endpoint | Uso |
|--------|----------|-----|
| GET | `/api/v1/produtos/?q={texto}` | Busca produtos por nome ou marca |
| GET | `/api/v1/supermercados/` | Lista supermercados ativos |
| GET | `/api/v1/produtos/{id}/comparacao/` | Preço mais recente em cada supermercado |
| GET | `/api/v1/produtos/{id}/historico/?supermercado_id={id}` | Histórico de preços |
| POST | `/api/v1/listas/simular/` | Total previsto da lista por supermercado |

Os formatos de entrada e saída são os da seção 11 da especificação: campos em
`snake_case` sem acento, datas em ISO 8601 com fuso e valores monetários como
string decimal (`"24.90"`).

## Decisões de contrato tomadas no backend

Pontos que a especificação não fechava e que precisam ir para o `docs/api.md`:

1. **Comparação – supermercado sem preço (CT-04).** Todo supermercado ativo
   aparece na lista `precos`. Quando não há oferta ou preço, o item vem com
   `"disponivel": false` e `valor`, `data_hora_coleta` e `url_fonte` nulos.
   Quando há preço, `"disponivel": true`.

   ```json
   {
     "supermercado": {"id": 3, "nome": "Mercado C"},
     "disponivel": false,
     "valor": null,
     "data_hora_coleta": null,
     "url_fonte": null
   }
   ```

2. **RN-10 – uma oferta ativa por produto e supermercado.** Podem existir
   várias `OfertaFonte` para o mesmo par Produto + Supermercado, mas somente
   uma com `ativo = true`. O model rejeita ativar uma segunda. Comparação e
   simulação usam sempre a oferta ativa.

3. **Busca sem `q`.** `GET /api/v1/produtos/` sem o parâmetro `q` (ou com `q`
   vazio) retorna todos os produtos, ordenados por nome.

4. **Histórico.** A resposta é `{"produto": {...}, "historico": [...]}`, com os
   registros do mais antigo para o mais recente. Cada registro tem
   `supermercado`, `valor`, `data_hora_coleta` e `url_fonte`. O filtro
   `supermercado_id` é opcional; vazio é o mesmo que não enviar.

5. **Simulação – subtotais por item.** Além dos campos do exemplo 11.2, cada
   supermercado traz `itens`, com o valor unitário e o subtotal de cada produto
   encontrado naquele mercado (os ausentes continuam em `itens_ausentes`):

   ```json
   "itens": [
     {"produto_id": 101, "quantidade": 2, "valor_unitario": "24.90", "subtotal": "49.80"},
     {"produto_id": 205, "quantidade": 1, "valor_unitario": "17.90", "subtotal": "17.90"}
   ]
   ```

6. **Simulação – erros de entrada.** Lista vazia, quantidade fora do intervalo
   1 a 1000 ou `produto_id` inexistente retornam `400` com a mensagem do campo.


## Coleta e atualização de preços

As integrações estão em `coleta/` e podem ser executadas em modo de simulação ou gravação.

Atualização conjunta das três redes:

```bash
python manage.py atualizar_precos_todos --cep 14010000
python manage.py atualizar_precos_todos --cep 14010000 --gravar
```

Também permanecem disponíveis os comandos individuais de Savegnago, Atacadão e Carrefour, além de comandos específicos de importação e conciliação. A rotina agendada atualiza apenas ofertas já existentes. As alterações de valor geram registros históricos; observações de valores inalterados podem ser registradas uma vez ao dia após consulta real. A gravação local não altera o banco de produção.

## Integração contínua

O workflow `.github/workflows/ci.yml` executa automaticamente os testes do backend com PostgreSQL, o build do frontend e o build Docker em Pull Requests e pushes para a `main`. Consulte o [README principal](../README.md) para fluxo de deploy e diferenças entre produção e desenvolvimento.
