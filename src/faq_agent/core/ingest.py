"""Script de ingestão: lê o documento, vetoriza e grava no Autonomous Database.

Destino no seu repo: src/faq_agent/core/ingest.py

Uso (a partir da raiz do repo, com o pacote instalado em modo editável):
    python -m faq_agent.core.ingest data/faq_pagamentos.pdf

Rodar sempre que o documento fonte mudar.
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple

from pypdf import PdfReader

from faq_agent import config
from faq_agent.clients import db_client as db
from faq_agent.clients import oci_client

CHUNK_MAX_CHARS = 1200
EMBED_BATCH_SIZE = 90  # limite prático por chamada ao serviço de embeddings


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def split_into_chunks(text: str, max_chars: int = CHUNK_MAX_CHARS) -> List[Tuple[str, str]]:
    """Divide o texto em chunks por seção (títulos numerados tipo '12. Alterações...'),
    e dentro de cada seção quebra por parágrafo até caber em max_chars.
    Retorna lista de (titulo_da_secao, texto_do_chunk).
    """
    section_pattern = re.compile(r"^\s*(\d{1,2}(?:\.\d{1,2})?)\.\s+(.+)$", re.MULTILINE)

    matches = list(section_pattern.finditer(text))
    sections: List[Tuple[str, str]] = []

    if not matches:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        sections = [("Documento", p) for p in paragraphs]
    else:
        for i, match in enumerate(matches):
            title = f"{match.group(1)}. {match.group(2)}".strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            if body:
                sections.append((title, body))

    chunks: List[Tuple[str, str]] = []
    for title, body in sections:
        if len(body) <= max_chars:
            chunks.append((title, body))
            continue
        paragraphs = [p.strip() for p in body.split("\n") if p.strip()]
        buffer = ""
        for paragraph in paragraphs:
            if len(buffer) + len(paragraph) + 1 > max_chars and buffer:
                chunks.append((title, buffer.strip()))
                buffer = ""
            buffer += paragraph + "\n"
        if buffer.strip():
            chunks.append((title, buffer.strip()))

    return chunks


def batched(items: List, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main(pdf_path: str) -> None:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    print(f"Extraindo texto de {path} ...")
    text = extract_text(path)

    print("Dividindo em chunks ...")
    chunks = split_into_chunks(text)
    print(f"{len(chunks)} chunks gerados.")

    print("Recriando schema no banco ...")
    db.create_schema()

    client = oci_client.get_genai_client()

    print("Gerando embeddings e gravando no banco ...")
    total_inserted = 0
    for batch in batched(chunks, EMBED_BATCH_SIZE):
        texts = [content for _, content in batch]
        embeddings = oci_client.embed_texts(client, texts, input_type="SEARCH_DOCUMENT")
        rows = [
            (title, content, embedding)
            for (title, content), embedding in zip(batch, embeddings)
        ]
        db.insert_chunks(rows)
        total_inserted += len(rows)
        print(f"  ... {total_inserted}/{len(chunks)} chunks gravados")

    print("Ingestão concluída.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m faq_agent.core.ingest <caminho_do_pdf>")
        sys.exit(1)
    main(sys.argv[1])
