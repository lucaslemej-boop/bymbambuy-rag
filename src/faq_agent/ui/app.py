"""Interface Streamlit do agente de FAQ.

Destino no seu repo: src/faq_agent/ui/app.py

Rodar (a partir da raiz do repo): streamlit run src/faq_agent/ui/app.py
"""
import streamlit as st

from faq_agent.core import rag

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
            try:
                answer, contexts = rag.answer_question(question)
            except Exception as exc:  # noqa: BLE001
                answer = f"Erro ao consultar o agente: {exc}"
                contexts = []
        st.markdown(answer)
        if contexts:
            with st.expander("Trechos do FAQ usados na resposta"):
                for title, content in contexts:
                    st.markdown(f"**{title}**\n\n{content}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
