from groq import Groq
from google import genai
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

Cuando respondas:
- Usá un tono cálido y didáctico, como un mentor barista
- Sé preciso con los parámetros técnicos (temperatura, ratio, tiempo)
- Si tenés recetas propias del café, priorizalas sobre el conocimiento genérico
- Citá las fuentes cuando uses información de los documentos
- Si no sabés algo, decilo honestamente
- Respondé siempre en español
- Mantené las respuestas concisas pero completas"""

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
        self.genai_client = genai.Client(
            api_key=Config.GOOGLE_API_KEY,
        )
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)

    def build_context(self, query: str) -> tuple[str, list[str]]:
        intents = detect_intent(query)
        logger.info(f"Intents detectados: {intents}")

        context_parts = []
        sources = []

        # Buscar recetas propias primero
        own_recipes = self.recipe_manager.search_recipes(query)
        if own_recipes:
            recipes_context = self.recipe_manager.format_recipes_context(own_recipes)
            context_parts.append(f"RECETAS PROPIAS DEL CAFÉ:\n{recipes_context}")
            sources.append("Recetas propias")
            logger.info(f"Recetas propias encontradas: {len(own_recipes)}")

        # Buscar en documentos del knowledge base
        doc_results = self.document_manager.search(query, top_k=Config.TOP_K_RESULTS)
        if doc_results:
            docs_context = self.document_manager.format_context(doc_results)
            context_parts.append(f"CONOCIMIENTO TÉCNICO:\n{docs_context}")
            for doc in doc_results:
                source = doc.get("metadata", {}).get("source", "")
                if source and source not in sources:
                    sources.append(source)

        return "\n\n".join(context_parts), sources

    def chat(self, query: str, history: list[dict] = None) -> tuple[str, list[str]]:
        history = history or []
        logger.info(f"Query: '{query[:80]}'")

        context, sources = self.build_context(query)

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
        return answer, sources
