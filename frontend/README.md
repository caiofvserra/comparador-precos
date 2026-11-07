# Frontend - Comparador de Preços

Interface web do Projeto Integrador II, desenvolvida com Vue 3, TypeScript, Vite e Vue Router.

## Requisitos

- Node.js compatível com `package.json`
- npm
- Backend Django em execução para trabalhar com dados reais

## Configuração

Na pasta `frontend`:

```bash
npm install
```

Copie o arquivo de ambiente:

```bash
cp .env.example .env
```

No Windows:

```powershell
Copy-Item .env.example .env
```

Para consumir a API real:

```env
VITE_API_URL=http://localhost:8000
```

Sem `VITE_API_URL`, a aplicação entra em modo demonstrativo com dados locais.

## Desenvolvimento

```bash
npm run dev
```

A aplicação fica normalmente em `http://localhost:5173/`.

## Build

```bash
npm run build
```

O comando executa a verificação de tipos e gera a versão otimizada para produção.

## Funcionalidades

- pesquisa de produtos;
- comparação de preços entre supermercados;
- histórico de preços;
- lista de compras temporária;
- comparação dos totais por supermercado;
- indicação de lista completa/incompleta;
- links para as fontes e para os sites dos supermercados;
- imagens reais da API quando disponíveis, com fallback ilustrativo;
- layout responsivo para desktop e celular.

## Dados

Com a API configurada, o frontend utiliza os dados do PostgreSQL expostos pelo Django REST Framework. As imagens reais retornadas pela API têm prioridade sobre os fallbacks locais.

## Validação

O GitHub Actions executa `npm run build` automaticamente em Pull Requests e pushes para a `main`.
