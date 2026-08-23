"""Conexão com a Autonomous Database 26ai e operações de vector store.

Destino no seu repo: src/faq_agent/clients/db_client.py
"""
import array
import logging
from contextlib import contextmanager
from typing import Iterable, List, Tuple

import oracledb

from faq_agent import config
from faq_agent.errors import DatabaseError

logger = logging.getLogger(__name__)

TABLE_NAME = "faq_chunks"


@contextmanager
def get_connection():
    try:
        connection = oracledb.connect(
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            dsn=config.DB_DSN,
            config_dir=config.DB_WALLET_DIR,
            wallet_location=config.DB_WALLET_DIR,
            wallet_password=config.DB_WALLET_PASSWORD,
        )
    except oracledb.Error as exc:
        logger.exception("Falha ao conectar no Autonomous Database")
        message = str(exc)
        if "DPY-6000" in message or "DPY-6005" in message:
            raise DatabaseError(
                "Não foi possível conectar ao Autonomous Database. Verifique se a instância "
                "está com status 'Available' no console OCI (bancos Always Free param "
                "automaticamente após 7 dias sem uso) e se o DB_DSN no .env está correto."
            ) from exc
        if "ORA-01017" in message:
            raise DatabaseError(
                "Usuário ou senha do banco incorretos. Confira DB_USER e DB_PASSWORD no .env."
            ) from exc
        raise DatabaseError(f"Erro ao conectar ao banco: {message}") from exc

    try:
        yield connection
    finally:
        connection.close()


def create_schema() -> None:
    """Cria a tabela de chunks/embeddings, se ainda não existir."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                declare
                    table_missing exception;
                    pragma exception_init(table_missing, -942);
                begin
                    execute immediate 'drop table {TABLE_NAME}';
                exception
                    when table_missing then null;
                end;
                """
            )
            cur.execute(
                f"""
                create table {TABLE_NAME} (
                    id number generated always as identity primary key,
                    section_title varchar2(500),
                    content clob not null,
                    embedding vector({config.EMBED_DIMENSIONS}, float32) not null
                )
                """
            )
        conn.commit()


def insert_chunks(rows: Iterable[Tuple[str, str, List[float]]]) -> None:
    """rows: lista de (section_title, content, embedding)."""
    rows = list(rows)
    if not rows:
        return
    with get_connection() as conn:
        with conn.cursor() as cur:
            data = [
                (title, content, array.array("f", embedding))
                for title, content, embedding in rows
            ]
            try:
                cur.executemany(
                    f"insert into {TABLE_NAME} (section_title, content, embedding) "
                    f"values (:1, :2, :3)",
                    data,
                )
            except oracledb.Error as exc:
                logger.exception("Falha ao gravar chunks no banco")
                raise DatabaseError(
                    f"Erro ao gravar {len(data)} chunk(s) no banco: {exc}"
                ) from exc
        conn.commit()


def search_similar(query_embedding: List[float], top_k: int) -> List[Tuple[str, str]]:
    """Retorna [(section_title, content), ...] mais próximos da pergunta."""
    qvec = array.array("f", query_embedding)
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    f"""
                    select section_title, content
                    from {TABLE_NAME}
                    order by vector_distance(embedding, :qvec, COSINE)
                    fetch first :top_k rows only
                    """,
                    qvec=qvec,
                    top_k=top_k,
                )
            except oracledb.Error as exc:
                logger.exception("Falha ao buscar chunks similares")
                message = str(exc)
                if "ORA-00942" in message:
                    raise DatabaseError(
                        "A tabela do vector store ainda não existe. Rode "
                        "'python -m faq_agent.core.ingest <pdf>' antes de usar o chat."
                    ) from exc
                raise DatabaseError(f"Erro ao buscar contexto no banco: {message}") from exc

            results = []
            for section_title, content in cur.fetchall():
                text = content.read() if hasattr(content, "read") else content
                results.append((section_title, text))
            return results
