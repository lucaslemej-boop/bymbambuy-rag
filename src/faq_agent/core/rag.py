"""Camada de RAG: recebe uma pergunta, busca contexto no vector store e chama o LLM.

Destino no seu repo: src/faq_agent/core/rag.py
"""
from typing import List, Tuple

from faq_agent import config
from faq_agent.clients import db_client as db
from faq_agent.clients import oci_client

SYSTEM_PROMPT = (
    "Você é um agente de atendimento interno que responde perguntas de colaboradores "
    "com base SOMENTE no contexto fornecido, extraído do FAQ oficial da empresa. "
    "Se a resposta não estiver no contexto, diga claramente que não encontrou essa "
    "informação no documento e sugira contatar a área responsável. "
    "Nunca invente políticas, prazos ou valores que não estejam no contexto. "
    "Responda em português, de forma direta e objetiva."
)


def build_prompt(question: str, contexts: List[Tuple[str, str]]) -> str:
    context_block = "\n\n".join(
        f"[Seção: {title}]\n{content}" for title, content in contexts
    )
    return (
        f"Contexto recuperado do FAQ:\n{context_block}\n\n"
        f"Pergunta do colaborador: {question}\n\n"
        f"Responda com base apenas no contexto acima."
    )


def answer_question(question: str) -> Tuple[str, List[Tuple[str, str]]]:
    client = oci_client.get_genai_client()

    query_embedding = oci_client.embed_texts(
        client, [question], input_type="SEARCH_QUERY"
    )[0]

    contexts = db.search_similar(query_embedding, top_k=config.TOP_K)

    if not contexts:
        return (
            "Não encontrei nenhuma informação relacionada no FAQ. "
            "Recomendo contatar o suporte responsável.",
            [],
        )

    prompt = build_prompt(question, contexts)
    answer = oci_client.chat(client, SYSTEM_PROMPT, prompt)
    return answer, contexts
