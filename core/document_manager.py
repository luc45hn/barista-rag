from supabase import create_client
from google import genai
from google.genai import types
from core.config import Config
from core.logger import get_logger

logger = get_logger("document_manager")

class DocumentManager:
    def __init__(self):
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        embedding_key = Config.GOOGLE_EMBEDDING_KEY or Config.GOOGLE_API_KEY
        self.genai_client = genai.Client(
            api_key=embedding_key,
            http_options={"api_version": "v1"}
        )

    def get_embedding(self, text: str) -> list[float]:
        result = self.genai_client.models.embed_content(
            model=Config.EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=768
            )
        )
        return result.embeddings[0].values

    def search(self, query: str, top_k: int = None, cafe_id: str = "") -> list[dict]:
        top_k = top_k or Config.TOP_K_RESULTS
        logger.info(f"Buscando: '{query[:60]}...'")
        logger.info(f"Buscando con cafe_id: '{cafe_id}'")

        query_embedding = self.get_embedding(query)

        params = {
            "query_embedding": query_embedding,
            "match_count": top_k,
        }
        if cafe_id:
            params["filter_cafe_id"] = cafe_id

        response = self.supabase.rpc("match_documents", params).execute()

        results = response.data or []
        logger.info(f"Encontrados {len(results)} chunks relevantes")
        return results

    def format_context(self, results: list[dict]) -> str:
        if not results:
            return ""

        context_parts = []
        for i, doc in enumerate(results, 1):
            source = doc.get("metadata", {}).get("source", "desconocido")
            content = doc.get("content", "")
            context_parts.append(f"[Fuente {i}: {source}]\n{content}")

        return "\n\n---\n\n".join(context_parts)
