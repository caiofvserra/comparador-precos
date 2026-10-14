# Comparador de Preços de Supermercados

Aplicação web desenvolvida como Projeto Integrador para pesquisar produtos, comparar preços entre supermercados, consultar históricos e simular listas de compras.

O projeto também conta com uma integração de coleta de dados do **Savegnago**, permitindo importar produtos e registrar atualizações de preços.

## Tecnologias

### Frontend
- Vue 3
- TypeScript
- Vite
- Vue Router

### Backend
- Python
- Django
- Django REST Framework
- PostgreSQL
- Requests para consultas à fonte de dados do Savegnago

## Funcionalidades

- Busca e listagem de produtos.
- Comparação de preços entre supermercados.
- Consulta do histórico de preços.
- Simulação do custo de uma lista de compras.
- Identificação de produtos indisponíveis.
- Exibição de imagens dos produtos.
- Importação de produtos e ofertas do Savegnago.
- Registro histórico de alterações de preços.

## Estrutura do projeto

```text
comparador-precos/
├── backend/
│   ├── catalogo/
│   ├── coleta/
│   │   └── management/
│   │       └── commands/
│   ├── config/
│   ├── precos/
│   ├── simulacao/
│   ├── tests/
│   ├── .env.example
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   ├── .env.example
│   └── package.json
├── docs/
└── README.md
```

## Requisitos

Antes de começar, instale:

- Python 3.11 ou superior.
- Node.js compatível com a versão exigida em `frontend/package.json`.
- npm.
- PostgreSQL.
- Git.

## Como executar no Windows

### 1. Configurar o banco de dados

Crie um usuário e um banco PostgreSQL para o projeto. Se ainda não existirem, execute no PostgreSQL:

```sql
CREATE USER comparador WITH PASSWORD 'comparador' CREATEDB;
CREATE DATABASE comparador OWNER comparador;
```

Se o usuário ou banco já existir, não execute novamente os comandos correspondentes. Verifique as permissões e a configuração existentes.

### 2. Configurar o backend

Na raiz do projeto, execute:

```powershell
cd backend

py -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt

Copy-Item .env.example .env
```

Edite `backend/.env` e confira as configurações do Django e do PostgreSQL. Os valores do arquivo devem corresponder ao banco criado na etapa anterior.

Execute as migrações:

```powershell
python manage.py migrate
```

Inicie o servidor:

```powershell
python manage.py runserver
```

A API ficará disponível em:

`http://localhost:8000/api/v1/`

Para acessar o Django Admin, crie um usuário administrativo:

```powershell
python manage.py createsuperuser
```

O painel ficará disponível em `http://localhost:8000/admin/`.

### 3. Configurar o frontend

Abra outro terminal PowerShell na raiz do projeto:

```powershell
cd frontend

Copy-Item .env.example .env

npm install
npm run dev
```

Confira se `frontend/.env` contém a URL correta da API:

```env
VITE_API_URL=http://localhost:8000
```

O Vite exibirá no terminal o endereço local do frontend, normalmente:

`http://localhost:5173/`

Mantenha os servidores do backend e do frontend em execução enquanto utiliza a aplicação.

## Integração com o Savegnago

A integração utiliza os comandos de gerenciamento do Django localizados em `backend/coleta/management/commands/`.

Os exemplos abaixo devem ser executados na raiz do projeto, com o ambiente virtual do backend disponível.

### Importar produtos e ofertas

Por exemplo, para pesquisar arroz:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\manage.py importar_savegnago --termo "arroz" --quantidade 10 --cep 14010000
```

Por padrão, o comando executa uma simulação: os dados não são gravados no banco.

Para gravar os dados:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\manage.py importar_savegnago --termo "arroz" --quantidade 10 --cep 14010000 --gravar
```

Substitua o termo pela categoria ou produto desejado. A quantidade define o limite de resultados solicitado, conforme o funcionamento do coletor.

### Atualizar preços cadastrados

Para simular uma atualização dos preços das ofertas ativas do Savegnago:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_savegnago
```

Para gravar as alterações encontradas:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_savegnago --gravar
```

O comando consulta os produtos associados às ofertas ativas, valida os dados obtidos e registra um novo histórico quando identifica alteração de preço.

### Atualização periódica

A atualização pode ser automatizada pelo Agendador de Tarefas do Windows.

Exemplo de configuração:

- **Programa:** caminho completo para `backend\.venv\Scripts\python.exe`.
- **Argumentos:** `backend\manage.py atualizar_precos_savegnago --gravar`.
- **Iniciar em:** caminho completo para a pasta raiz do projeto.
- **Periodicidade:** conforme a necessidade de atualização.

A tarefa agendada é uma configuração local do Windows e não é compartilhada automaticamente pelo Git. Cada integrante deve configurá-la em seu próprio computador, caso deseje automatizar as atualizações.

## Endpoints principais

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/produtos/` | Lista e pesquisa produtos |
| GET | `/api/v1/supermercados/` | Lista supermercados ativos |
| GET | `/api/v1/produtos/{id}/comparacao/` | Compara os preços de um produto |
| GET | `/api/v1/produtos/{id}/historico/` | Consulta o histórico de preços |
| POST | `/api/v1/listas/simular/` | Simula uma lista de compras |

Para detalhes sobre os formatos das requisições e respostas, consulte a documentação do backend e os arquivos disponíveis em `docs/`.

## Testes

Para verificar a configuração do Django:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\manage.py check
```

Para executar os testes da integração de importação do Savegnago:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\manage.py test tests.test_importar_savegnago -v 2
```

## Boas práticas

- Não versione arquivos `.env`, senhas, tokens ou outras credenciais.
- Mantenha as dependências documentadas nos arquivos `requirements.txt` e `package.json`.
- Execute os testes antes de enviar alterações.
- Desenvolva novas funcionalidades em branches específicas.
- Não execute comandos de importação com `--gravar` em um ambiente compartilhado sem entender quais dados serão alterados.

## Documentação complementar

- `backend/README.md`: configuração, API e detalhes técnicos do backend.
- `frontend/README.md`: ambiente de desenvolvimento do frontend.
- `docs/README.md`: visão geral e documentação do projeto.
