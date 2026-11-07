🛒 Comparador de Preços de Supermercados

<p align="center">
  <strong>Compare preços, economize nas compras e encontre as melhores ofertas!</strong>
</p>

<p align="center">
  Aplicação web desenvolvida como Projeto Integrador, com integração de dados de três redes de supermercados: Savegnago, Atacadão e Carrefour.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Django-5.1-green?logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/Vue.js-3-42b883?logo=vuedotjs&logoColor=white" alt="Vue.js">
  <img src="https://img.shields.io/badge/TypeScript-blue?logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/PostgreSQL-Database-4169e1?logo=postgresql&logoColor=white" alt="PostgreSQL">
</p>

📌 Sobre o projeto

O Comparador de Preços de Supermercados é uma aplicação web desenvolvida para facilitar a pesquisa de produtos, a comparação de preços e o planejamento de compras.

O sistema reúne informações de diferentes supermercados, permitindo consultar ofertas, acompanhar o histórico de preços e simular o custo de listas de compras.

Atualmente, o projeto possui integração com três redes:

Supermercado

Integração

🟢 Savegnago

Coleta e atualização de preços

🔵 Atacadão

Coleta, conciliação e atualização de preços

🔴 Carrefour

Coleta, identificação por EAN e atualização de preços

✨ Funcionalidades

🔎 Pesquisa e listagem de produtos.

💰 Comparação de preços entre supermercados.

📊 Consulta do histórico de preços.

🛒 Simulação do custo de uma lista de compras.

🚫 Identificação de produtos indisponíveis.

🖼️ Exibição de imagens dos produtos.

🔄 Integração com Savegnago, Atacadão e Carrefour.

📦 Importação e conciliação de produtos e ofertas.

⏰ Atualização automática de preços.

📈 Registro histórico de alterações de preços.

🧰 Tecnologias utilizadas

Frontend

Tecnologia

Utilização

Vue 3

Construção da interface

TypeScript

Tipagem e organização do código

Vite

Ambiente de desenvolvimento e build

Vue Router

Navegação entre páginas

Backend

Tecnologia

Utilização

Python

Linguagem principal

Django

Framework backend

Django REST Framework

Construção da API

PostgreSQL

Banco de dados relacional

Requests

Consultas às fontes de dados dos supermercados

📁 Estrutura do projeto

comparador-precos/
│
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
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── .env.example
│   └── package.json
│
├── docs/
│
└── README.md

🚀 Instalação e execução

📋 Requisitos

Antes de iniciar, instale:

Python 3.11 ou superior.

Node.js compatível com a versão exigida em frontend/package.json.

npm.

PostgreSQL.

Git.

1️⃣ Configuração do banco de dados

Crie um usuário e um banco PostgreSQL para o projeto.

Caso ainda não existam, execute:

CREATE USER comparador WITH PASSWORD 'comparador' CREATEDB;
CREATE DATABASE comparador OWNER comparador;

⚠️ Se o usuário ou banco já existir, não execute novamente os comandos correspondentes. Verifique as permissões e configurações existentes.

2️⃣ Configuração do backend

Na raiz do projeto, abra o PowerShell e execute:

cd backend

py -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt

Copy-Item .env.example .env

Edite o arquivo backend/.env e configure as variáveis necessárias para o Django e o PostgreSQL.

Execute as migrações:

python manage.py migrate

Crie um usuário administrativo:

python manage.py createsuperuser

Inicie o servidor:

python manage.py runserver

Endereços disponíveis:

API: http://localhost:8000/api/v1/

Django Admin: http://localhost:8000/admin/

3️⃣ Configuração do frontend

Abra outro terminal PowerShell na raiz do projeto:

cd frontend

Copy-Item .env.example .env

npm install
npm run dev

Confira se o arquivo frontend/.env contém a URL correta da API:

VITE_API_URL=http://localhost:8000

A aplicação ficará disponível normalmente em:

http://localhost:5173/

💡 Mantenha os servidores do backend e do frontend em execução enquanto utiliza a aplicação.

🏪 Integração com supermercados

As integrações são implementadas por comandos de gerenciamento do Django, localizados em:

backend/coleta/management/commands/

Os comandos devem ser executados na raiz do projeto, utilizando o interpretador Python do ambiente virtual.

⚠️ Importante: os comandos de coleta e conciliação que oferecem suporte à simulação não gravam alterações no banco por padrão. Utilize --gravar somente depois de conferir os resultados.

🟢 1. Savegnago

A integração permite pesquisar produtos, importar ofertas e atualizar preços cadastrados.

📦 Importar produtos e ofertas

Exemplo de pesquisa por arroz:

.\backend\.venv\Scripts\python.exe .\backend\manage.py importar_savegnago --termo "arroz" --quantidade 10 --cep 14010000

Para gravar os dados:

.\backend\.venv\Scripts\python.exe .\backend\manage.py importar_savegnago --termo "arroz" --quantidade 10 --cep 14010000 --gravar

🔄 Atualizar preços cadastrados

Simulação:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_savegnago

Gravação:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_savegnago --gravar

🔵 2. Atacadão

A integração realiza consultas de produtos e ofertas no Atacadão, utilizando o código de barras para identificar correspondências.

🔗 Conciliar produtos e ofertas

Simulação:

.\backend\.venv\Scripts\python.exe .\backend\manage.py conciliar_atacadao --quantidade 20

Gravação:

.\backend\.venv\Scripts\python.exe .\backend\manage.py conciliar_atacadao --quantidade 20 --gravar

O comando também permite utilizar filtros como --limite, --offset e --ean.

A conciliação considera a compatibilidade de marca e nome dos produtos para reduzir associações incorretas.

🔄 Atualizar preços cadastrados

Simulação:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_atacadao --cep 14010-000

Gravação:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_atacadao --cep 14010-000 --gravar

🔴 3. Carrefour

A integração consulta os produtos disponíveis no site do Carrefour, utilizando informações estruturadas das páginas dos produtos para identificar código de barras, nome, marca, disponibilidade e preço.

🔎 Pesquisar produtos

Exemplo de pesquisa por arroz:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_carrefour --termo "arroz" --quantidade 10

Para gravar os resultados:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_carrefour --termo "arroz" --quantidade 10 --gravar

🏷️ Consultar produto pelo EAN

Consulta específica:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_carrefour --ean 7896006716150

Para gravar o resultado:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_carrefour --ean 7896006716150 --gravar

🔄 Atualizar todas as ofertas cadastradas

Simulação:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_carrefour --todos

Gravação:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_carrefour --todos --gravar

🔁 Atualizar as três redes em uma única execução

Simulação:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_todos --cep 14010000

Gravação:

.\backend\.venv\Scripts\python.exe .\backend\manage.py atualizar_precos_todos --cep 14010000 --gravar

O comando executa Savegnago, Atacadão e Carrefour em sequência e informa eventuais falhas sem interromper as demais redes.

⏰ Atualização automática de preços

As atualizações periódicas dos três supermercados são executadas pelo Agendador de Tarefas do Windows.

Atualmente, as tarefas estão organizadas da seguinte maneira:

Supermercado

Tarefa agendada

Horário aproximado

🟢 Savegnago

Atualizar Preços Savegnago

12:30

🔵 Atacadão

Atualizar Preços Atacadão

12:45

🔴 Carrefour

Atualizar Preços Carrefour

13:00

As tarefas utilizam o interpretador Python do ambiente virtual e executam os respectivos comandos de atualização com a opção --gravar.

⚙️ Configuração das tarefas

Para configurar uma tarefa no Windows, utilize:

Programa: caminho completo para backend\.venv\Scripts\python.exe.

Argumentos: comando Django correspondente, incluindo --gravar.

Iniciar em: caminho completo para a pasta raiz do projeto.

Periodicidade: diária, conforme o horário desejado.

💡 A configuração do Agendador de Tarefas é local do Windows e não é compartilhada automaticamente pelo Git. O computador precisa estar ligado e conectado à internet no horário programado.

🧪 Testes

Para verificar a configuração do Django:

.\backend\.venv\Scripts\python.exe .\backend\manage.py check

Para executar todos os testes automatizados:

.\backend\.venv\Scripts\python.exe .\backend\manage.py test tests

Os testes verificam o funcionamento das funcionalidades implementadas no backend. A execução dos testes não realiza atualizações reais de preços nos supermercados.

O repositório também possui GitHub Actions para executar automaticamente os testes do backend com PostgreSQL e o build do frontend em Pull Requests e pushes para a main.

🔌 Endpoints principais da API

Método

Endpoint

Descrição

GET

/api/v1/produtos/

Lista e pesquisa produtos

GET

/api/v1/supermercados/

Lista supermercados ativos

GET

/api/v1/produtos/{id}/comparacao/

Compara preços de um produto

GET

/api/v1/produtos/{id}/historico/

Consulta histórico de preços

POST

/api/v1/listas/simular/

Simula uma lista de compras

Para detalhes sobre os formatos das requisições e respostas, consulte a documentação do backend e os arquivos disponíveis em docs/.

🛡️ Boas práticas

Não versione arquivos .env, senhas, tokens ou outras credenciais.

Mantenha as dependências documentadas nos arquivos requirements.txt e package.json.

Execute os testes antes de enviar alterações.

Desenvolva novas funcionalidades em branches específicas.

Execute os comandos de coleta em modo de simulação antes de utilizar --gravar.

Não execute comandos de gravação em um ambiente compartilhado sem entender quais dados serão alterados.

Confira os resultados das atualizações e os registros históricos de preços.

📚 Documentação complementar

Arquivo

Descrição

backend/README.md

Configuração, API e detalhes técnicos do backend

frontend/README.md

Ambiente de desenvolvimento do frontend

docs/README.md

Visão geral e documentação do projeto

<p align="center">
  <strong>🛒 Comparador de Preços de Supermercados</strong>
  <br>
  Projeto Integrador — Engenharia da Computação
</p>