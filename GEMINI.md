# Visão Geral do Projeto Mech-AI

Mech-AI é uma aplicação web full-stack projetada para auxiliar oficinas automotivas no registro eficiente de detalhes de serviços. Ela utiliza a IA Google Gemini para processar descrições de serviços em linguagem natural, extrair informações chave e armazená-las em um banco de dados estruturado.

## Arquitetura

O projeto consiste em duas partes principais:

1.  **Backend (Python FastAPI):**
    *   Construído com FastAPI, fornecendo uma API robusta para gerenciar registros de serviços e integração com IA.
    *   Usa SQLAlchemy com `aiosqlite` para operações assíncronas de banco de dados, armazenando registros de serviços em um banco de dados SQLite.
    *   Integra-se com a API Google Gemini via `utils/gemini_service.py` para interpretar descrições de serviços.
    *   A configuração é gerenciada por meio de variáveis de ambiente carregadas de um arquivo `.env` usando `python-dotenv`.
    *   Modelos: `models.py` define o modelo SQLAlchemy `ServiceRecord`.

2.  **Frontend (React.js):**
    *   Uma aplicação de página única construída com React.js, fornecendo uma interface de chat intuitiva para os usuários interagirem com o assistente Mech-AI.
    *   Comunica-se com o backend FastAPI para enviar mensagens do usuário e receber dados de serviço estruturados.
    *   Desenvolvido usando Create React App (`react-scripts`).

## Funcionalidades

*   **Registro de Serviço com IA:** Os usuários podem descrever serviços automotivos em linguagem natural, e a IA Gemini extrai detalhes relevantes como veículo, tipo de serviço, data, custo e observações.
*   **Armazenamento de Dados Estruturados:** As informações de serviço extraídas são armazenadas em um banco de dados SQLite.
*   **Interface de Chat:** Uma interface de chat amigável permite uma interação perfeita com o assistente de IA.

## Tecnologias Utilizadas

### Backend

*   **Python:** Linguagem de Programação
*   **FastAPI:** Framework Web
*   **SQLAlchemy:** ORM para interação com banco de dados
*   **aiosqlite:** Driver SQLite assíncrono
*   **API Google Gemini (`google-generativeai`):** Modelo de IA para processamento de linguagem natural
*   **python-dotenv:** Gerenciamento de variáveis de ambiente
*   **Uvicorn:** Servidor ASGI

### Frontend

*   **React.js:** Biblioteca JavaScript para construção de interfaces de usuário
*   **JavaScript:** Linguagem de Programação
*   **HTML/CSS:** Conteúdo e estilização web
*   **react-scripts (Create React App):** Ferramenta de build do frontend

## Construindo e Executando o Projeto

### Pré-requisitos

*   Python 3.8+
*   Node.js e npm (ou yarn)
*   Uma Chave de API Google Gemini (definida no seu arquivo `.env`)

### 1. Configuração do Backend

Navegue até o diretório raiz do projeto (`mech_ai/`).

#### Instalar Dependências

```bash
pip install -r requirements.txt
```

#### Configuração do Ambiente

Crie um arquivo `.env` na raiz do projeto com sua chave de API Gemini:

```
GEMINI_API_KEY="SUA_CHAVE_API_GEMINI"
```

#### Executar o Backend

```bash
uvicorn app_fastapi:app --reload
```

A API do backend estará disponível em `http://127.0.0.1:8000`.

### 2. Configuração do Frontend

Navegue até o diretório `frontend`:

```bash
cd frontend
```

#### Instalar Dependências

```bash
npm install
```

#### Executar o Frontend

```bash
npm start
```

O servidor de desenvolvimento React será iniciado, geralmente abrindo em seu navegador em `http://localhost:3000`.

## Convenções de Desenvolvimento

*   **Backend:** Segue as melhores práticas de Python e as convenções do FastAPI. A programação assíncrona é usada para interações com banco de dados e API.
*   **Frontend:** Adere à arquitetura baseada em componentes do React.
*   **Comunicação da API:** O frontend se comunica com o backend por meio de chamadas de API RESTful.
*   **Formatação de Código:** Espera-se que as convenções de formatação padrão de Python e JavaScript sejam seguidas.
*   **Banco de Dados:** SQLite é usado para desenvolvimento local e pode ser facilmente trocado por outros bancos de dados com SQLAlchemy.

## Estrutura do Projeto

```
mech_ai/
├── .env                      # Variáveis de ambiente
├── app_fastapi.py            # Aplicação principal FastAPI
├── config.py                 # Configurações
├── database.py               # Inicialização do banco de dados e gerenciamento de sessão
├── mech_ai.db                # Arquivo de banco de dados SQLite
├── models.py                 # Modelos de banco de dados SQLAlchemy
├── requirements.txt          # Dependências Python
├── frontend/                 # Aplicação frontend React
│   ├── public/               # Ativos públicos
│   ├── src/                  # Código fonte React
│   │   ├── components/       # Componentes React reutilizáveis (ex: Chat, Message)
│   │   ├── App.js            # Componente React principal
│   │   └── index.js          # Ponto de entrada React
│   ├── package.json          # Dependências e scripts do frontend
│   └── ...
├── routers/                  # Definições de rota FastAPI
│   ├── chat.py               # Endpoints da API de chat
│   └── services.py           # Endpoints da API relacionados a serviços (não totalmente explorados)
└── utils/                    # Funções utilitárias
    └── gemini_service.py     # Integração com a API Google Gemini
```