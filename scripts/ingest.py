import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from supabase import create_client
from google import genai
from google.genai import types
from core.config import Config
from core.logger import get_logger

logger = get_logger("ingest")

def get_embedding(client: genai.Client, text: str) -> list[float]:
    result = client.models.embed_content(
        model=Config.EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=768
        )
    )
    return result.embeddings[0].values

def chunk_markdown(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    lines = text.split("\n")
    chunks = []
    current_chunk = []
    current_size = 0
    current_header = ""

    for line in lines:
        if line.startswith("#"):
            current_header = line.strip()

        line_size = len(line)

        if current_size + line_size > chunk_size and current_chunk:
            chunk_text = "\n".join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)
            overlap_lines = current_chunk[-3:]
            current_chunk = [current_header] + overlap_lines if current_header else overlap_lines
            current_size = sum(len(l) for l in current_chunk)

        current_chunk.append(line)
        current_size += line_size

    if current_chunk:
        chunk_text = "\n".join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks

def ingest_documents():
    Config.validate()
    client = genai.Client(api_key=Config.GOOGLE_API_KEY,
                          http_options={"api_version": "v1"})
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

    kb_path = Path(Config.KNOWLEDGE_BASE_DIR)
    md_files = sorted(kb_path.glob("*.md"))

    if not md_files:
        logger.error(f"No se encontraron archivos .md en {kb_path}")
        return

    logger.info(f"Encontrados {len(md_files)} archivos para ingestar")

    supabase.table("documents").delete().neq("id", 0).execute()
    logger.info("Tabla documents limpiada")

    total_chunks = 0

    for md_file in md_files:
        logger.info(f"Procesando: {md_file.name}")
        text = md_file.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)

        for i, chunk in enumerate(chunks):
            embedding = get_embedding(client, chunk)
            supabase.table("documents").insert({
                "content": chunk,
                "metadata": {
                    "source": md_file.name,
                    "chunk_index": i,
                },
                "embedding": embedding,
            }).execute()
            logger.info(f"  chunk {i+1}/{len(chunks)} subido")

        total_chunks += len(chunks)
        logger.info(f"  {md_file.name} → {len(chunks)} chunks")

    logger.info(f"Ingesta completa: {total_chunks} chunks totales")

if __name__ == "__main__":
    ingest_documents()
