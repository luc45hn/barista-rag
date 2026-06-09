import io
import time
from supabase import create_client
from google import genai
from google.genai import types
from core.config import Config
from core.logger import get_logger

logger = get_logger("document_ingestor")

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

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
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

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extrayendo texto del PDF: {e}")
        return ""

def ingest_user_document(
    file_bytes: bytes,
    filename: str,
    cafe_id: str,
    uploaded_by: str,
) -> dict:
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    embedding_key = Config.GOOGLE_EMBEDDING_KEY or Config.GOOGLE_API_KEY
    genai_client = genai.Client(
        api_key=embedding_key,
        http_options={"api_version": "v1"}
    )

    # Extraer texto según el formato
    if filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith((".md", ".txt")):
        text = file_bytes.decode("utf-8", errors="ignore")
    else:
        return {"success": False, "error": "Formato no soportado. Usá PDF o Markdown."}

    if not text.strip():
        return {"success": False, "error": "No se pudo extraer texto del documento."}

    # Subir archivo a Storage
    storage_path = f"{cafe_id}/{filename}"
    try:
        supabase.storage.from_("user-documents").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": "application/octet-stream", "upsert": "true"}
        )
    except Exception as e:
        logger.error(f"Error subiendo archivo a Storage: {e}")
        return {"success": False, "error": "Error subiendo el archivo."}

    # Registrar en tabla user_documents
    doc_response = supabase.table("user_documents").insert({
        "cafe_id": cafe_id,
        "uploaded_by": uploaded_by,
        "filename": filename,
        "storage_path": storage_path,
        "approved": False,
    }).execute()

    if not doc_response.data:
        return {"success": False, "error": "Error registrando el documento."}

    doc_id = doc_response.data[0]["id"]

    # Generar chunks y embeddings
    chunks = chunk_text(text, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
    logger.info(f"Documento '{filename}' → {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(genai_client, chunk)
        supabase.table("documents").insert({
            "content": chunk,
            "metadata": {
                "source": filename,
                "cafe_id": cafe_id,
                "user_document_id": doc_id,
                "chunk_index": i,
                "approved": False,
            },
            "embedding": embedding,
        }).execute()
        time.sleep(2)  # evitar rate limit
        logger.info(f"  chunk {i+1}/{len(chunks)} procesado")

    logger.info(f"Documento '{filename}' ingestado — {len(chunks)} chunks, pendiente de aprobación")
    return {"success": True, "doc_id": doc_id, "chunks": len(chunks)}

def approve_user_document(doc_id: str, approved_by: str) -> bool:
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

    # Actualizar user_documents
    supabase.table("user_documents").update({
        "approved": True,
        "approved_by": approved_by
    }).eq("id", doc_id).execute()

    # Activar chunks — actualizar metadata para marcarlos como aprobados
    docs = supabase.table("documents").select("id, metadata").execute()
    for doc in docs.data or []:
        if doc.get("metadata", {}).get("user_document_id") == doc_id:
            updated_metadata = {**doc["metadata"], "approved": True}
            supabase.table("documents").update({
                "metadata": updated_metadata
            }).eq("id", doc["id"]).execute()

    logger.info(f"Documento {doc_id} aprobado por {approved_by}")
    return True

def delete_user_document(doc_id: str, storage_path: str) -> bool:
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

    # Eliminar chunks de documents
    docs = supabase.table("documents").select("id, metadata").execute()
    for doc in docs.data or []:
        if doc.get("metadata", {}).get("user_document_id") == doc_id:
            supabase.table("documents").delete().eq("id", doc["id"]).execute()

    # Eliminar de Storage
    try:
        supabase.storage.from_("user-documents").remove([storage_path])
    except Exception as e:
        logger.warning(f"Error eliminando archivo de Storage: {e}")

    # Eliminar de user_documents
    supabase.table("user_documents").delete().eq("id", doc_id).execute()
    logger.info(f"Documento {doc_id} eliminado")
    return True
