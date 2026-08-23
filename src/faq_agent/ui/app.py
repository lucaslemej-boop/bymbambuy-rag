"""Interface Streamlit do agente de FAQ."""
import logging

import streamlit as st

from faq_agent.core import rag
from faq_agent.errors import FaqAgentError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="BimBam Buy | Central de pagamentos",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --ink: #16232b;
        --muted: #66747a;
        --paper: #f7f8f4;
        --line: #dce3df;
        --mint: #d7f4df;
        --green: #13795b;
        --orange: #f6a34b;
    }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: #102d2c;
        border-right: 0;
    }
    [data-testid="stSidebar"] * { color: #edf6ef; }
    [data-testid="stSidebar"] .stButton button {
        background: rgba(255,255,255,.09);
        border: 1px solid rgba(255,255,255,.15);
        color: #fff;
    }
    [data-testid="stSidebar"] .stButton button:hover { background: rgba(255,255,255,.16); }
    h1, h2, h3, [data-testid="stChatMessage"] p { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: var(--ink); }
    .brand-mark {
        display: inline-flex; align-items: center; justify-content: center;
        width: 42px; height: 42px; border-radius: 12px; background: var(--orange);
        color: #102d2c; font-size: 22px; font-weight: 700; margin-bottom: 18px;
    }
    .eyebrow { color: var(--green); font-size: 12px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
    .hero { padding: 38px 0 22px; max-width: 760px; }
    .hero h1 { font-size: clamp(2rem, 4vw, 3.45rem); line-height: 1.02; margin: 8px 0 14px; letter-spacing: 0; }
    .hero p { color: var(--muted); font-size: 1.05rem; line-height: 1.55; max-width: 660px; }
    .status {
        display: inline-flex; align-items: center; gap: 8px; padding: 7px 11px;
        border: 1px solid var(--line); border-radius: 999px; color: var(--muted);
        font-size: 12px; background: rgba(255,255,255,.65);
    }
    .status-dot { width: 7px; height: 7px; background: #32a56f; border-radius: 50%; }
    .welcome-panel {
        border: 1px solid var(--line); border-radius: 10px; padding: 24px;
        background: #fff; margin: 12px 0 22px;
    }
    .welcome-panel h3 { margin: 0 0 5px; font-size: 1.1rem; }
    .welcome-panel p { color: var(--muted); margin: 0; }
    [data-testid="stChatMessage"] { border-radius: 10px; padding: 12px 16px; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { line-height: 1.6; }
    [data-testid="stChatInput"] { border-top: 0; }
    [data-testid="stChatInput"] textarea { font-family: 'DM Sans', sans-serif; }
    .source-label { color: var(--muted); font-size: 12px; margin: 4px 0 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown('<div class="brand-mark">bb</div>', unsafe_allow_html=True)
    st.markdown("## Central de pagamentos")
    st.caption("Respostas rápidas para as dúvidas do dia a dia.")
    if st.button("＋  Nova conversa", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.markdown("**Assuntos frequentes**")
    st.caption("Escolha um tema para começar")
    sidebar_topics = {
        "Pagamentos": "Como funciona o pagamento por boleto?",
        "Reembolsos": "Como solicitar um reembolso?",
        "Cancelamentos": "Qual é a política de cancelamento?",
        "Cobranças": "Quais são os prazos de cobrança?",
    }
    for label, prompt in sidebar_topics.items():
        if st.button(label, key=f"topic_{label}", use_container_width=True):
            st.session_state.pending_question = prompt
            st.rerun()
    st.divider()
    st.caption("Base de conhecimento")
    st.markdown("**FAQ oficial**  \n<small>Busca semântica no Oracle Database</small>", unsafe_allow_html=True)

st.markdown(
    '<div class="hero"><div class="eyebrow">BimBam Buy · suporte interno</div>'
    '<h1>Encontre a resposta certa para cada pagamento.</h1>'
    '<p>Consulte o FAQ oficial sobre pagamentos, reembolsos, cancelamentos e cobranças. '
    'Faça uma pergunta do seu jeito.</p></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="status"><span class="status-dot"></span> Base oficial · busca semântica no Oracle Database</div>',
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown(
        '<div class="welcome-panel"><h3>Por onde começamos?</h3>'
        '<p>Selecione uma sugestão ou escreva sua dúvida abaixo.</p></div>',
        unsafe_allow_html=True,
    )
    suggested_questions = [
        "Como funciona o pagamento por boleto?",
        "Existe reembolso para uma compra cancelada?",
        "Qual é a política de cancelamento?",
    ]
    columns = st.columns(3)
    for column, prompt in zip(columns, suggested_questions):
        with column:
            if st.button(prompt, key=f"suggestion_{prompt}", use_container_width=True):
                st.session_state.pending_question = prompt
                st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ex.: como funciona o pagamento por boleto?")
if st.session_state.get("pending_question"):
    question = st.session_state.pop("pending_question")

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
            with st.expander("Ver fontes consultadas"):
                st.markdown('<div class="source-label">Trechos recuperados do FAQ oficial</div>', unsafe_allow_html=True)
                for title, content in contexts:
                    st.markdown(f"**{title}**\n\n{content}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
