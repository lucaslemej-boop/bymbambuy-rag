"""Clientes OCI (Generative AI) e helpers de embedding/chat.

Destino no seu repo: src/faq_agent/clients/oci_client.py
"""
import logging
from typing import List

import oci

from faq_agent import config
from faq_agent.errors import GenAIError

logger = logging.getLogger(__name__)


def get_genai_client() -> oci.generative_ai_inference.GenerativeAiInferenceClient:
    try:
        oci_config = oci.config.from_file(
            file_location=config.OCI_CONFIG_FILE, profile_name=config.OCI_CONFIG_PROFILE
        )
    except oci.exceptions.ConfigFileNotFound as exc:
        logger.exception("Config file da OCI não encontrado")
        raise GenAIError(
            f"Arquivo de configuração da OCI não encontrado em {config.OCI_CONFIG_FILE}. "
            f"Confira se o ~/.oci/config existe no servidor."
        ) from exc

    try:
        return oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=oci_config,
            service_endpoint=(
                f"https://inference.generativeai.{oci_config['region']}.oci.oraclecloud.com"
            ),
        )
    except KeyError as exc:
        raise GenAIError(
            "O arquivo ~/.oci/config não tem a chave 'region' preenchida corretamente."
        ) from exc


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
    try:
        response = client.embed_text(embed_text_details=details)
    except oci.exceptions.ServiceError as exc:
        logger.exception("Erro do serviço OCI Generative AI (embed_text)")
        raise GenAIError(
            "Não foi possível gerar o embedding no momento. "
            f"O serviço OCI Generative AI respondeu com erro {exc.status}: {exc.message}."
        ) from exc
    except oci.exceptions.RequestException as exc:
        logger.exception("Falha de rede ao chamar embed_text")
        raise GenAIError(
            "Não foi possível conectar ao serviço OCI Generative AI. "
            "Verifique a conexão do servidor com a internet e tente novamente."
        ) from exc

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

    try:
        response = client.chat(chat_details=details)
    except oci.exceptions.ServiceError as exc:
        logger.exception("Erro do serviço OCI Generative AI (chat)")
        if exc.status == 404:
            raise GenAIError(
                "O modelo de chat configurado (CHAT_MODEL_ID) não foi encontrado. "
                "Confira se o OCID no .env está correto e completo (começando com 'ocid1.')."
            ) from exc
        raise GenAIError(
            f"Não foi possível obter resposta do modelo de chat (erro {exc.status}: {exc.message})."
        ) from exc
    except oci.exceptions.RequestException as exc:
        logger.exception("Falha de rede ao chamar chat")
        raise GenAIError(
            "Não foi possível conectar ao serviço OCI Generative AI. Tente novamente em instantes."
        ) from exc

    try:
        choice = response.data.chat_response.choices[0]
        parts = choice.message.content
        return "".join(part.text for part in parts if getattr(part, "type", "TEXT") == "TEXT")
    except (IndexError, AttributeError) as exc:
        logger.exception("Resposta do modelo de chat em formato inesperado")
        raise GenAIError(
            "O modelo respondeu em um formato inesperado. Tente novamente."
        ) from exc
