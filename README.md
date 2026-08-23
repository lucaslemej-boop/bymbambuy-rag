# Agente FAQ com RAG

Este projeto é um exemplo simples de agente RAG para responder perguntas sobre o FAQ da BimBam Buy.
A ideia é ler um documento em PDF, transformar o texto em embeddings, salvar esses trechos em um banco vetorial e, depois, buscar as partes mais relevantes para responder a pergunta do usuário.

Foi feito como projeto de estudo para aprender o fluxo completo de um sistema RAG usando Python, Oracle Database e OCI Generative AI.

## O que esse projeto faz

- lê um PDF com o FAQ
- quebra o texto em partes menores
- gera embeddings com o OCI
- salva os trechos no Oracle Autonomous Database
- recebe a pergunta do usuário
- busca os blocos mais parecidos
- monta um prompt com esse contexto
- retorna a resposta no chat

## Como funciona

```text
PDF do FAQ
   ↓
extração do texto
   ↓
quebra em chunks
   ↓
geração de embeddings
   ↓
armazenamento no Oracle
   ↓
pergunta do usuário
   ↓
busca semântica
   ↓
resposta com contexto
```

## Estrutura do projeto

```text
bymbambuy-rag/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env
├── .env.example
├── .gitignore
├── data/
│   └── FAQ-BimBam-Buy.pdf
├── docs/
│   └── arquivos de apoio do projeto
├── src/
│   └── faq_agent/
│       ├── __init__.py
│       ├── config.py
│       ├── clients/
│       │   ├── __init__.py
│       │   ├── db_client.py
│       │   └── oci_client.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── ingest.py
│       │   └── rag.py
│       └── ui/
│           ├── __init__.py
│           └── app.py
└── wallet/
    └── Wallet_faqragdb/
```

## Tecnologias usadas

- Python 3.11+
- Streamlit
- OCI SDK
- Oracle Database / Oracle Autonomous Database
- pypdf
- python-dotenv

## Pré-requisitos

Antes de rodar o projeto, você precisa ter:

- conta na Oracle Cloud Infrastructure (OCI)
- Autonomous Database criada
- wallet do banco baixado e extraído
- acesso ao OCI Generative AI
- arquivo de configuração da OCI em `~/.oci/config`
- um arquivo `.env` com as variáveis de conexão

## Configuração do ambiente

1. Crie o ambiente virtual:

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
```

No Linux/Mac:

```bash
source .venv/bin/activate
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Copie o arquivo de exemplo:

```bash
copy .env.example .env
```

ou no Linux/Mac:

```bash
cp .env.example .env
```

4. Preencha o `.env` com os dados reais do seu ambiente.

As variáveis principais são:

- `OCI_COMPARTMENT_ID`
- `CHAT_MODEL_ID`
- `DB_PASSWORD`
- `DB_DSN`
- `DB_WALLET_DIR`
- `DB_WALLET_PASSWORD`

Você pode conferir o modelo de exemplo em [.env.example](.env.example).

## Como rodar o projeto localmente

### 1. Ingerir o PDF no banco

A partir da raiz do projeto:

```bash
python -m faq_agent.core.ingest data/FAQ-BimBam-Buy.pdf
```

Esse passo lê o PDF, separa em partes e grava os embeddings no banco.

### 2. Subir a interface

```bash
streamlit run src/faq_agent/ui/app.py
```

Depois, abra o endereço exibido no terminal no navegador.

## Como o app é usado

Na interface do Streamlit, você digita uma pergunta como:

- "Como funciona o pagamento por boleto?"
- "Existe reembolso?"
- "Qual a política de cancelamento?"

O agente busca o conteúdo mais relevante no banco vetorial e responde com base no FAQ.

A interface foi organizada para ficar mais simples de usar, com menu lateral, sugestões de perguntas e respostas destacadas em uma cor diferente.

## Observações importantes

- o arquivo do FAQ usado no projeto está em `data/FAQ-BimBam-Buy.pdf`
- o script de ingestão está em `src/faq_agent/core/ingest.py`
- a interface está em `src/faq_agent/ui/app.py`
- o código de busca e resposta está em `src/faq_agent/core/rag.py`

- ## Evidencias do deploy e do projeto funcionando

Autonomous Database usado na OCI
<img width="1912" height="988" alt="image" src="https://github.com/user-attachments/assets/40580e6a-bba1-4237-8ebf-8af1d612be23" />

Servidor Linux usado para o Deploy da aplicação
<img width="1911" height="681" alt="image" src="https://github.com/user-attachments/assets/2354e8bd-952a-4106-9363-346c8a63c60c" />

