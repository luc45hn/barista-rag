from groq import Groq
from google import genai
from supabase import create_client
from core.config import Config
from core.document_manager import DocumentManager
from core.recipe_manager import RecipeManager
from core.logger import get_logger

logger = get_logger("consultant_agent")

SYSTEM_PROMPT = """Sos Barista IA, un asistente experto en café de especialidad para baristas en entrenamiento.

Tu conocimiento incluye:
- Técnicas de preparación: espresso, V60, Chemex, Kalita Wave, AeroPress, French Press, Cold Brew
- Estándares SCA (Specialty Coffee Association)
- Perfiles de sabor y orígenes del café
- Ciencia de la extracción: TDS, ratio, temperatura, molienda
- Técnicas de vaporizado y latte art
- Resolución de problemas y defectos

Cuando respondás:
- Usá un tono cálido y didáctico, como un mentor barista
- Sé preciso con los parámetros técnicos (temperatura, ratio, tiempo)
- Respondé con conocimiento técnico claro y conciso
- NO incluyas recetas de usuarios en tu respuesta — esas se mostrarán por separado
- Si no sabés algo, decilo honestamente
- Respondé siempre en español"""

INTENT_KEYWORDS = {
    "recipe": ["receta", "cómo preparo", "cómo hago", "parámetros", "ratio",
               "dosis", "temperatura", "tiempo", "gramos", "v60", "chemex",
               "aeropress", "espresso", "cappuccino", "latte", "cold brew",
               "french press", "kalita", "filtrado"],
    "troubleshoot": ["ácido", "amargo", "astringente", "salado", "plano",
                     "defecto", "problema", "error", "mal", "raro", "extraño",
                     "corregir", "arreglar", "mejorar", "channeling"],
    "origin": ["origen", "país", "etiopía", "colombia", "brasil", "kenia",
               "guatemala", "sumatra", "proceso", "lavado", "natural", "honey",
               "variedad", "altitude", "altitud"],
    "sensory": ["sabor", "aroma", "notas", "perfil", "cata", "cupping",
                "dulce", "floral", "frutal", "chocolate", "nuez", "acidez"],
}

def detect_intent(query: str) -> list[str]:
    query_lower = query.lower()
    intents = []
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            intents.append(intent)
    return intents if intents else ["general"]

class ConsultantAgent:
    def __init__(self):
        self.document_manager = DocumentManager()
        self.recipe_manager = RecipeManager()
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
        self.genai_client = genai.Client(api_key=Config.GOOGLE_API_KEY)
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    def build_context(self, query: str, cafe_id: str = "") -> tuple[str, list[str], list[str], list[dict]]:
        intents = detect_intent(query)
        logger.info(f"Intents detectados: {intents}")

        context_parts = []
        sources = []

        doc_results = self.document_manager.search(query, top_k=Config.TOP_K_RESULTS)
        if doc_results:
            docs_context = self.document_manager.format_context(doc_results)
            context_parts.append(f"CONOCIMIENTO TÉCNICO:\n{docs_context}")
            for doc in doc_results:
                source = doc.get("metadata", {}).get("source", "")
                if source and source not in sources:
                    sources.append(source)

        related_recipes = self.recipe_manager.search_related_recipes(query, cafe_id=cafe_id)

        return "\n\n".join(context_parts), sources, intents, related_recipes

    def chat(self, query: str, history: list[dict] = None, user_email: str = "", cafe_id: str = "") -> tuple[str, list[str], list[dict]]:
        history = history or []
        logger.info(f"Query: '{query[:80]}'")

        context, sources, intents, related_recipes = self.build_context(query, cafe_id=cafe_id)

        user_message = query
        if context:
            user_message = f"""Contexto relevante:
{context}

Pregunta: {query}"""

        groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history[-6:]:
            groq_messages.append({
                "role": msg["role"] if msg["role"] == "user" else "assistant",
                "content": msg["content"]
            })
        groq_messages.append({"role": "user", "content": user_message})

        response = self.groq_client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=groq_messages,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS,
        )

        answer = response.choices[0].message.content
        logger.info(f"Respuesta generada ({len(answer)} chars)")

        try:
            self.supabase.table("query_logs").insert({
                "user_email": user_email,
                "query": query,
                "intents": intents,
                "chunks_found": len(sources),
                "had_own_recipes": len(related_recipes) > 0,
            }).execute()
        except Exception as e:
            logger.warning(f"No se pudo guardar el log: {e}")

        return answer, sources, related_recipes
