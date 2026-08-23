"""Exceções próprias do agente, para diferenciar erros esperados (mensagem amigável
pro usuário) de bugs inesperados (que devem ser logados, não expostos crus na UI).

Destino no seu repo: src/faq_agent/errors.py
"""


class FaqAgentError(Exception):
    """Erro esperado do domínio da aplicação — a mensagem é segura para mostrar ao usuário."""


class GenAIError(FaqAgentError):
    """Falha ao chamar o OCI Generative AI (embedding ou chat)."""


class DatabaseError(FaqAgentError):
    """Falha ao conectar ou consultar o Autonomous Database."""


class InvalidQuestionError(FaqAgentError):
    """Pergunta do usuário inválida (vazia, curta demais, etc.)."""
