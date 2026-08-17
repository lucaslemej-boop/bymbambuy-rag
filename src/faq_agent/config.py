"""Configuração centralizada do agente RAG.

Lê tudo de variáveis de ambiente (.env local ou variáveis exportadas no servidor).
Nada de segredo fica hardcoded no código.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Variável de ambiente obrigatória '{name}' não encontrada. "
            f"Confira seu arquivo .env (veja .env.example)."
        )
    return value


# --- OCI (config/API key para chamar o Generative AI) ---
OCI_CONFIG_FILE = os.getenv("OCI_CONFIG_FILE", os.path.expanduser("~/.oci/config"))
OCI_CONFIG_PROFILE = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
OCI_COMPARTMENT_ID = _require("OCI_COMPARTMENT_ID")

# Modelos usados no OCI Generative AI.
# Pegue os IDs exatos clicando em "View code" no playground do Chat/Embedding no console OCI.
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID", "cohere.embed-v4.0")
CHAT_MODEL_ID = _require("CHAT_MODEL_ID")
EMBED_DIMENSIONS = int(os.getenv("EMBED_DIMENSIONS", "1024"))

# --- Autonomous Database 26ai (wallet mTLS) ---
DB_USER = os.getenv("DB_USER", "ADMIN")
DB_PASSWORD = _require("DB_PASSWORD")
DB_DSN = _require("DB_DSN")  # ex: "faqragdb_high" (alias do tnsnames.ora dentro do wallet)
DB_WALLET_DIR = _require("DB_WALLET_DIR")  # pasta onde o wallet.zip foi extraído
DB_WALLET_PASSWORD = _require("DB_WALLET_PASSWORD")

# --- Aplicação ---
TOP_K = int(os.getenv("TOP_K", "4"))
DATA_DIR = os.getenv("DATA_DIR", "data")
