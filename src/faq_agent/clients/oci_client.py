"""Clientes OCI (Generative AI) e helpers de embedding/chat.

Destino no seu repo: src/faq_agent/clients/oci_client.py
"""
from typing import List

import oci

from faq_agent import config


def get_genai_client() -> oci.generative_ai_inference.GenerativeAiInferenceClient:
    oci_config = oci.config.from_file(
        file_location=config.OCI_CONFIG_FILE, profile_name=config.OCI_CONFIG_PROFILE
    )
    # O endpoint de inferência do Generative AI é regional; o SDK já resolve
    # a partir da região presente no ~/.oci/config.
    return oci.generative_ai_inference.GenerativeAiInferenceClient(
        config=oci_config,
        service_endpoint=f"https://inference.generativeai.{oci_config['region']}.oci.oraclecloud.com",
    )


def embed_texts(client, texts: List[str], input_type: str) -> List[List[float]]:
    """Gera embeddings para uma lista de textos.

    input_type: "SEARCH_DOCUMENT" para chunks armazenados, "SEARCH_QUERY" para a pergunta do usuário.
    """
    details = oci.generative_ai_inference.models.EmbedTextDetails(
        serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
            serving_type="ON_DEMAND",
            model_id=config.EMBED_MODEL_ID,
        ),
        compartment_id=config.OCI_COMPARTMENT_ID,
        inputs=texts,
        input_type=input_type,
        truncate="END",
        output_dimensions=config.EMBED_DIMENSIONS,
    )
    response = client.embed_text(embed_text_details=details)
    return response.data.embeddings


def chat(client, system_prompt: str, user_prompt: str, max_tokens: int = 600) -> str:
    """Chama o modelo de chat configurado (ex: google.gemini-2.5-flash) com um prompt simples."""
    messages = [
        oci.generative_ai_inference.models.SystemMessage(
            role="SYSTEM",
            content=[oci.generative_ai_inference.models.TextContent(type="TEXT", text=system_prompt)],
        ),
        oci.generative_ai_inference.models.UserMessage(
            role="USER",
            content=[oci.generative_ai_inference.models.TextContent(type="TEXT", text=user_prompt)],
        ),
    ]

    chat_request = oci.generative_ai_inference.models.GenericChatRequest(
        api_format="GENERIC",
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.2,
        is_stream=False,
    )

    details = oci.generative_ai_inference.models.ChatDetails(
        compartment_id=config.OCI_COMPARTMENT_ID,
        serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
            serving_type="ON_DEMAND",
            model_id=config.CHAT_MODEL_ID,
        ),
        chat_request=chat_request,
    )

    response = client.chat(chat_details=details)

    # A forma de extrair o texto varia um pouco conforme o provedor do modelo (Cohere, Meta, Google...).
    # Para api_format="GENERIC", a resposta traz "choices" com "message.content".
    choice = response.data.chat_response.choices[0]
    parts = choice.message.content
    return "".join(part.text for part in parts if getattr(part, "type", "TEXT") == "TEXT")
