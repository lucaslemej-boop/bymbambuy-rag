# Status do Projeto — Agente RAG FAQ (BimBam Buy) — Alura Challenge

Atualizado em: 02/08/2026

## Contexto

Desafio Alura Agentes: criar um agente de IA em Python que responde perguntas de
colaboradores com base num FAQ interno (documento: FAQ de Métodos de Pagamento da
BimBam Buy). Requisitos do desafio: repositório público no GitHub, deploy na OCI
usando ao menos um serviço Oracle, README com imagem/vídeo do agente rodando na nuvem.
Requisito adicional do próprio Lucas: aplicação em Python (não low-code/n8n).

**Decisão sobre n8n:** avaliado e descartado para o núcleo do projeto — entra em
conflito com o requisito de vetorização por código em Python. Poderia ser usado só
para automações periféricas (não implementado).

## Arquitetura decidida

- Vector store + serviço OCI principal: **Oracle Autonomous Database 26ai** (o que era
  chamado de "23ai" foi renomeado — só aparecia 19c e 26ai no console), com AI Vector
  Search, tier Always Free.
- Embeddings + LLM: **OCI Generative AI**, modelo de embedding `cohere.embed-v4.0`
  (multilíngue, confirmado suporte a português), modelo de chat testado no playground:
  `google.gemini-2.5-flash` (Lucas deve confirmar o `CHAT_MODEL_ID` exato via "View code"
  no console).
- Interface: **Streamlit** (decisão explicada e confirmada com Lucas).
- Hospedagem: **Compute Instance** na OCI, shape paga (não always-free) — motivo:
  A1 Flex e a AMD Always Free (E2.1.Micro) deram "out of capacity" repetidamente em
  Ashburn (problema conhecido e recorrente da OCI, não específico da conta). Custo
  coberto pelo crédito trial de US$300 (~R$1.500, expira 31/08/2026).
- Container Instances foi cogitado e descartado por complexidade desnecessária para
  um projeto de demo única (evitaria Docker/OCIR, mas não era necessário).

## Infraestrutura já provisionada (feito)

- Conta OCI criada do zero. Home region: **US East (Ashburn)**.
- Compute Instance `inst-vm01`, shape AMD paga (ex: VM.Standard.E4.Flex), Oracle Linux 9,
  **Running**. IP público: `129.80.1.38`. Usuário SSH: `opc`. Porta 8501 liberada no NSG
  (`ig-quick-action-NSG`) para o Streamlit. Conexão SSH já testada e funcionando.
- Autonomous Database 26ai provisionada (Always Free) — Lucas confirmou "banco no ar".
  Wallet já deve ter sido baixado (confirmar).
- OCI Generative AI testado com sucesso no playground (Chat com google.gemini-2.5-flash,
  Embedding com cohere.embed-v4.0). API Key gerada (arquivo `.pem` + bloco de config
  para `~/.oci/config`).

## Código já escrito (entregue no chat, salvo na pasta outputs)

Arquivos prontos: `config.py`, `oci_clients.py` (embed_text + chat via OCI GenAI),
`db.py` (conexão wallet + vector store no Autonomous DB), `ingest.py` (extração PDF +
chunking por seção + geração de embeddings + gravação no banco), `rag.py` (busca vetorial
+ prompt + resposta), `app.py` (Streamlit chat), `requirements.txt`, `.env.example`,
`.gitignore`, `README.md` (com arquitetura, setup, passo a passo de deploy e checklist
dos requisitos do desafio).

Também existe um `plano-projeto-rag.md` mais antigo (primeira versão do plano, já
superado em parte pelo README, mas com raciocínio de arquitetura ainda válido).

## Pendências / próximos passos

1. Colocar o PDF do FAQ na pasta `data/` do projeto (não foi copiado automaticamente
   por limitação técnica da sessão anterior).
2. Preencher o `.env` com: `OCI_COMPARTMENT_ID`, `CHAT_MODEL_ID` (pegar valor exato via
   "View code" no playground), dados do wallet (`DB_DSN`, `DB_WALLET_DIR`,
   `DB_WALLET_PASSWORD`, `DB_PASSWORD`).
3. Copiar projeto + wallet para o servidor via SCP (comandos já estão no README).
4. No servidor: instalar dependências, rodar `python ingest.py data/faq_pagamentos.pdf`
   para vetorizar, depois `streamlit run app.py --server.port 8501 --server.address 0.0.0.0`.
5. Testar acesso via `http://129.80.1.38:8501`.
6. Criar o repositório GitHub público, subir o código (conferir `.gitignore` já criado
   para não vazar `.env`/wallet).
7. Gravar imagem/vídeo do agente respondendo perguntas rodando no servidor, adicionar ao
   README (ainda pendente, marcado como não feito no checklist do README).
8. Depois de tudo validado manualmente: escrever o script Terraform equivalente (pedido
   original de Lucas, ainda não iniciado).

## Coisas para lembrar / armadilhas já descobertas

- OCI Generative AI **não é Always Free** (usa crédito trial ou pay-as-you-go depois).
- A1 Flex e AMD Micro Always Free têm escassez de capacidade crônica em Ashburn —
  não vale a pena insistir manualmente; shape paga resolve na hora.
- Ao criar VNIC/instância, o IP público não vem automático — precisa atribuir
  ephemeral public IP manualmente, e rodar a quick action "Connect public subnet to
  internet" para IGW/rotas/NSG.
- Regra de ingress no NSG: atenção para não inverter Source Port Range com
  Destination Port Range (Destination Port Range é a porta 8501 do servidor).
- Nome do banco mudou de "23ai" para "26ai" no console (mesma tecnologia, nome novo).
