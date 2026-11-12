# Frontend — Comparador de Preços

Interface **web responsiva** desenvolvida com Vue 3, TypeScript, Vite e Vue Router para o Projeto Integrador II.

**[Abrir aplicação publicada](https://comparador-precos-web-9j6z.onrender.com)** · [README principal](../README.md)

## Como funciona em produção

O `Dockerfile` constrói os arquivos do frontend e os integra à aplicação Django publicada no Render. **Frontend e API utilizam o mesmo endereço público**; não é necessário iniciar `npm run dev` nem manter um computador ligado para acessar o sistema.

- O build de produção usa `VITE_DEMO_MODE=false`: a interface consulta **dados reais disponibilizados pela API**, não mocks de demonstração.
- O endereço-base da API usa o mesmo domínio quando `VITE_API_URL` não está configurado (requisições relativas a `/api/v1/`).
- `CATALOGO_MODO=triangulacao` é enviado pelo backend via `GET /api/v1/configuracao/` e controla a priorização inicial de itens comparáveis nos três supermercados; não altera o trabalho dos coletores.

## Funcionalidades

- Pesquisa, filtros e listagem de produtos.
- Comparação de preços e identificação de ofertas indisponíveis.
- Histórico de preços com representação gráfica.
- Lista de compras com quantidade, subtotais e total por supermercado.
- Links para as fontes e supermercados.
- Imagens da API quando disponíveis, com fallback ilustrativo.
- Interface responsiva, inclusive menu de navegação adaptado a telas pequenas.

## Desenvolvimento local (opcional)

Requisitos: Node.js compatível com `package.json`, npm e API Django acessível.

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

No Windows, copie o ambiente com `Copy-Item .env.example .env`. O Vite normalmente estará em `http://localhost:5173/`. Para usar o backend local em outra porta, configure `VITE_API_URL=http://localhost:8000` no `frontend/.env`.

**Importante:** omitir `VITE_API_URL` **não** ativa os dados fictícios: apenas utiliza URLs relativas. Os dados de demonstração só são habilitados explicitamente com `VITE_DEMO_MODE=true`, em contexto local/ilustrativo.

## Build e validação

```bash
npm run build
```

A CI executa o build em Pull Requests e pushes à `main`. Depois de um merge, confira a nova versão em [Render → Deploys](https://dashboard.render.com/web/srv-dbnfnfbrjlhs738meva0); o merge não significa que o build já foi publicado.
