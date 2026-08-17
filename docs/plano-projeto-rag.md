# Agente RAG de FAQ — Plano do Projeto

## Visão geral

Agente de IA em Python que responde perguntas de colaboradores com base no FAQ de métodos de pagamento da BimBam Buy (ou outro documento interno equivalente). O documento é vetorizado por código, armazenado em um vector store na OCI, e as perguntas são respondidas via busca semântica + LLM. Interface em Streamlit. Deploy na OCI. Repositório público no GitHub.

## Arquitetura

```
Documento (PDF)
      │
      ▼
[ingest.py]  → extrai texto → chunking → embeddings (OCI Generative AI)
      │
      ▼
Oracle Autonomous Database 23ai (AI Vector Search)
      │
      ▼
[app.py - Streamlit]
   pergunta do usuário
      │
      ▼
   embedding da pergunta (OCI Generative AI)
      │
      ▼
   busca por similaridade no 23ai → top-k chunks
      │
      ▼
   prompt (contexto + pergunta) → LLM (OCI Generative AI)
      │
      ▼
   resposta exibida no chat
```

Serviço OCI usado de forma central (não só hospedagem): **Oracle Autonomous Database 23ai** para o vector store e **OCI Generative AI** para embeddings + geração de resposta. A aplicação Streamlit roda em uma **Compute Instance** (tier Always Free, VM.Standard.A1.Flex) ou em **Container Instances**.

## Stack tecnológica

- Python 3.11+
- `streamlit` — interface de chat
- `oracledb` (python-oracledb) — conexão com Autonomous DB 23ai e vector search
- `oci` (OCI Python SDK) — chamadas ao serviço OCI Generative AI (embeddings e chat)
- `pypdf` ou `pdfplumber` — extração de texto do PDF
- `python-dotenv` — variáveis de ambiente (chaves, connection string)

## Estrutura do repositório

```
faq-rag-agent/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── data/
│   └── faq_pagamentos.pdf
├── src/
│   ├── ingest.py          # extrai, chunka, gera embeddings, grava no 23ai
│   ├── rag.py             # busca vetorial + montagem de prompt + chamada ao LLM
│   ├── oci_clients.py     # inicialização dos clientes OCI (GenAI, DB)
│   └── config.py          # leitura de variáveis de ambiente
├── app.py                 # interface Streamlit
└── docs/
    └── demo.gif (ou link de vídeo)  # evidência do agente rodando na nuvem
```

## Passo a passo de implementação

1. **Setup OCI**
   - Criar conta/tenancy OCI (tier gratuito cobre Autonomous DB e Compute A1 Flex).
   - Provisionar uma Autonomous Database 23ai (Always Free).
   - Habilitar acesso ao serviço OCI Generative AI na região disponível (nem toda região tem o serviço — verificar).
   - Gerar credenciais (API key / config file `~/.oci/config`) para uso via SDK.

2. **Preparar o dado**
   - Colocar o PDF do FAQ em `data/`.
   - Extrair texto preservando a estrutura de seções (o documento já é bem numerado — dá pra chunkar por seção/subtítulo em vez de por tamanho fixo de caracteres, o que tende a gerar respostas mais precisas).

3. **Ingestão (`ingest.py`)**
   - Extrair texto → dividir em chunks por seção.
   - Gerar embedding de cada chunk via OCI Generative AI.
   - Criar tabela no 23ai com coluna `VECTOR` e gravar chunk + embedding + metadados (nº da seção, título).
   - Rodar uma vez (ou sempre que o documento mudar).

4. **Camada de busca e resposta (`rag.py`)**
   - Receber pergunta → gerar embedding da pergunta.
   - Rodar busca por similaridade (`VECTOR_DISTANCE` / índice HNSW no 23ai) e pegar top-k chunks.
   - Montar prompt: instrução + chunks recuperados + pergunta.
   - Chamar o modelo de chat da OCI Generative AI e retornar a resposta.
   - Importante: instruir o modelo a responder só com base no contexto recuperado e admitir quando não souber, para evitar alucinação fora do FAQ.

5. **Interface (`app.py`)**
   - Streamlit com `st.chat_input` / `st.chat_message` para simular um chat.
   - Chama `rag.py` a cada pergunta e exibe a resposta.

6. **Deploy na OCI**
   - Subir uma Compute Instance (A1 Flex, Always Free) ou Container Instance.
   - Instalar dependências, configurar variáveis de ambiente (connection string do 23ai, config OCI).
   - Rodar `streamlit run app.py --server.port 8501 --server.address 0.0.0.0` e liberar a porta no Security List/NSG.
   - (Opcional, mais robusto) colocar atrás de um Load Balancer OCI com HTTPS.

7. **GitHub**
   - Repositório público, código organizado conforme estrutura acima.
   - `.env.example` com as variáveis necessárias, sem segredos reais.
   - README com: descrição do projeto, arquitetura, como rodar localmente, como foi feito o deploy na OCI, e uma imagem/GIF ou vídeo do agente respondendo perguntas rodando na nuvem (requisito obrigatório do desafio).

## Sobre o n8n

Não entra no núcleo do projeto — o desafio pede vetorização por código e app em Python, e é essa parte que precisa ser demonstrada. Se quiser aproveitar sua instalação, o lugar razoável é em automações periféricas e opcionais, fora do caminho crítico de pergunta → resposta: por exemplo, um workflow que dispara `ingest.py` quando um novo documento é adicionado a uma pasta, ou que manda uma notificação quando o agente não encontra resposta no contexto. Colocar o n8n como orquestrador do fluxo de RAG em si aumentaria a complexidade de deploy (mais um serviço para hospedar e manter) sem ajudar a cumprir nenhum requisito do desafio.

## Checklist dos requisitos do desafio

- [ ] Repositório público no GitHub
- [ ] Documento vetorizado por código (não por serviço gerenciado de RAG pronto)
- [ ] Interface para o usuário perguntar e receber resposta
- [ ] Deploy na OCI usando ao menos um serviço Oracle (Autonomous DB 23ai + OCI Generative AI)
- [ ] README com imagem/vídeo do agente rodando na nuvem
