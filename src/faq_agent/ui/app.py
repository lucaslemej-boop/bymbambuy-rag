"""Interface Streamlit do agente de FAQ.

Destino no seu repo: src/faq_agent/ui/app.py

Rodar (a partir da raiz do repo): streamlit run src/faq_agent/ui/app.py
"""
import logging

import streamlit as st

from faq_agent.core import rag
from faq_agent.errors import FaqAgentError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Agente FAQ - BimBam Buy", page_icon="💬")
st.title("💬 Agente de FAQ — Métodos de Pagamento")
st.caption(
    "Pergunte sobre pagamentos, reembolsos, cancelamentos e cobranças. "
    "As respostas vêm do FAQ oficial, vetorizado no Oracle Autonomous Database."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Digite sua pergunta...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Consultando o FAQ..."):
            contexts = []
            try:
                answer, contexts = rag.answer_question(question)
            except FaqAgentError as exc:
                # Erro esperado do domínio: a mensagem já é segura pra mostrar.
                logger.warning("Erro de domínio ao responder pergunta: %s", exc)
                answer = f"⚠️ {exc}"
            except Exception:
                # Erro inesperado: loga o detalhe técnico, mas não expõe pro usuário.
                logger.exception("Erro inesperado ao responder pergunta")
                answer = (
                    "⚠️ Ocorreu um erro inesperado ao consultar o agente. "
                    "Tente novamente em instantes; se persistir, avise o time responsável."
                )
        st.markdown(answer)
        if contexts:
            with st.expander("Trechos do FAQ usados na resposta"):
                for title, content in contexts:
                    st.markdown(f"**{title}**\n\n{content}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
