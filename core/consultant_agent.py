from groq import Groq
from google import genai
from google.genai import types
from supabase import create_client
from core.config import Config
from core.document_manager import DocumentManager
from core.recipe_manager import RecipeManager
from core.logger import get_logger

logger = get_logger("consultant_agent")

SYSTEM_PROMPT = """Sos Barista IA, un asistente experto en café de especialidad para baristas en entrenamiento. Tu rol es el de un mentor barista experimentado — no solo informás, sino que razonás y recomendás.

## Cómo razonar ante cada pregunta

Antes de responder, conectá los datos disponibles en este orden:
1. **Si mencionan un origen o variedad de café** → describí primero el perfil de sabor esperado (acidez, dulzura, cuerpo, notas típicas)
2. **Conectá el perfil con los parámetros** → explicá por qué ese perfil requiere ciertos ajustes (ej: "como tiene alta acidez, bajá la temperatura para suavizarla")
3. **Considerá el objetivo de la preparación** → bebida sola, con leche, equilibrada, intensa
4. **Considerá las limitaciones del equipo** → qué variables están disponibles
5. **Recomendación concreta** → parámetros específicos con valores exactos, no rangos

## Adaptación al equipo

Cuando el usuario mencione su equipo o sus limitaciones:
- Trabajá dentro de esas limitaciones, no las ignorés
- Si no puede ajustar temperatura, enfocate en molienda, dosis y ratio
- Si no conocés el equipo específico, preguntá qué variables puede controlar
- Nunca recomendés algo que el usuario ya dijo que no puede hacer

## Formato de respuesta

- Empezá con el razonamiento: por qué el café se comporta de cierta manera
- Seguí con la recomendación: parámetros concretos (números, no rangos cuando sea posible)
- Cerrá con el próximo paso: qué ajustar primero si el resultado no es el esperado
- Si falta información clave para dar una recomendación precisa, hacé una sola pregunta

## Reglas generales

- Tono cálido y didáctico, como un mentor barista
- Respondé siempre en español
- NO incluyas recetas de usuarios en tu respuesta — esas se mostrarán por separado
- Si genuinamente no sabés algo, decilo y sugerí cómo encontrar la respuesta"""

INTENT_KEYWORDS = {
    "recipe": ["receta", "cómo preparo", "cómo hago", "parámetros", "ratio",
               "dosis", "temperatura", "tiempo", "gramos", "v60", "chemex",
               "aeropress", "espresso", "cappuccino", "latte", "cold brew",
               "french press", "kalita", "filtrado"],
    "troubleshoot": ["ácido", "amargo", "astringente", "salado", "plano",
                     "defecto", "problema", "error", "mal", "raro", "extraño",
                     "corregir", "arreglar", "mejorar", "channeling", "intenso"],
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
    def __init__(self, gemini_api_key: str = ""):
        self.document_manager = DocumentManager()
        self.recipe_manager = RecipeManager()
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
        self.gemini_api_key = gemini_api_key or Config.GOOGLE_API_KEY
        self.genai_client = None
        if self.gemini_api_key:
            self.genai_client = genai.Client(api_key=self.gemini_api_key)
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    def _generate_with_gemini(self, messages: list[dict]) -> str:
        gemini_messages = []
        system = None
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                gemini_messages.append(types.Content(
                    role=role,
                    parts=[types.Part(text=msg["content"])]
                ))
        response = self.genai_client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=gemini_messages,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=Config.TEMPERATURE,
                max_output_tokens=Config.MAX_TOKENS,
            )
        )
        return response.text

    def _generate_with_groq(self, messages: list[dict]) -> str:
        response = self.groq_client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=messages,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS,
        )
        return response.choices[0].message.content

    def _generate(self, messages: list[dict]) -> tuple[str, str]:
        if self.genai_client:
            try:
                answer = self._generate_with_gemini(messages)
                logger.info("Respuesta generada con Gemini Flash")
                return answer, "gemini"
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
                    logger.warning("Gemini quota agotada — fallback a Groq")
                else:
                    logger.warning(f"Error en Gemini ({e}) — fallback a Groq")
        answer = self._generate_with_groq(messages)
        logger.info("Respuesta generada con Groq/Llama")
        return answer, "groq"

    def build_context(self, query: str, cafe_id: str = "") -> tuple[str, list[str], list[str], list[dict]]:
        intents = detect_intent(query)
        logger.info(f"Intents detectados: {intents}")

        context_parts = []
        sources = []

        doc_results = self.document_manager.search(
            query,
            top_k=Config.TOP_K_RESULTS,
            cafe_id=cafe_id
        )
        if doc_results:
            docs_context = self.document_manager.format_context(doc_results)
            context_parts.append(f"CONOCIMIENTO TÉCNICO:\n{docs_context}")
            for doc in doc_results:
                source = doc.get("metadata", {}).get("source", "")
                if source and source not in sources:
                    sources.append(source)

        # Búsqueda híbrida — si detecta intent origin, forzar chunks de orígenes
        if "origin" in intents:
            origin_chunks = self.document_manager.search_by_source(
                query, "05_origenes_cafe", top_k=1
            )
            for chunk in origin_chunks:
                source = chunk.get("metadata", {}).get("source", "")
                if source not in sources:
                    doc_results.append(chunk)
                    if source:
                        sources.append(source)
            if origin_chunks:
                docs_context = self.document_manager.format_context(doc_results)
                context_parts = [f"CONOCIMIENTO TÉCNICO:\n{docs_context}"]

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

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history[-6:]:
            messages.append({
                "role": msg["role"] if msg["role"] == "user" else "assistant",
                "content": msg["content"]
            })
        messages.append({"role": "user", "content": user_message})

        answer, model_used = self._generate(messages)
        logger.info(f"Respuesta generada ({len(answer)} chars) via {model_used}")

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
