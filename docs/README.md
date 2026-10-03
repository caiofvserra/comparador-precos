# Comparador de Preços de Supermercados

Aplicação web para comparação de preços de produtos entre supermercados.

O sistema permite pesquisar produtos, comparar preços, consultar o histórico de preços e simular uma lista de compras com o valor estimado em cada supermercado.

## Tecnologias

### Backend

- Python
- Django
- Django REST Framework
- PostgreSQL

### Frontend

- Vue 3
- TypeScript
- Vite

## Funcionalidades

- Busca de produtos por nome ou marca
- Comparação de preços entre supermercados
- Histórico de preços
- Lista de compras
- Simulação do total por supermercado
- Identificação de itens indisponíveis
- Filtros de produtos
- Exibição de imagens dos produtos

## Estrutura

```text
comparador-precos/
├── backend/
│   ├── catalogo/
│   ├── coleta/
│   ├── config/
│   ├── precos/
│   ├── simulacao/
│   ├── tests/
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── composables/
│   │   ├── layouts/
│   │   ├── router/
│   │   ├── services/
│   │   └── views/
│   └── package.json
├── docs/
└── README.md
```

## Backend

Entre na pasta do backend:

```bash
cd backend
```

Crie e ative o ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie o arquivo de configuração:

```bash
cp .env.example .env
```

Execute as migrations:

```bash
python manage.py migrate
```

Para carregar os dados de exemplo:

```bash
python manage.py loaddata dados_exemplo
```

Inicie o servidor:

```bash
python manage.py runserver
```

A API ficará disponível em:

```text
http://localhost:8000/api/v1/
```

## Frontend

Entre na pasta do frontend:

```bash
cd frontend
```

Instale as dependências:

```bash
npm install
```

Crie o arquivo de configuração:

```bash
cp .env.example .env
```

Configure a URL da API no arquivo `.env`:

```env
VITE_API_URL=http://localhost:8000
```

Inicie o frontend:

```bash
npm run dev
```

## Endpoints principais

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/produtos/` | Lista e busca produtos |
| GET | `/api/v1/supermercados/` | Lista supermercados ativos |
| GET | `/api/v1/produtos/{id}/comparacao/` | Compara preços do produto |
| GET | `/api/v1/produtos/{id}/historico/` | Consulta o histórico de preços |
| POST | `/api/v1/listas/simular/` | Simula o valor da lista de compras |

## Testes

No diretório `backend`:

```bash
python manage.py check
python manage.py test
```
