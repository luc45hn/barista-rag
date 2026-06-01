import re
from supabase import create_client
from core.config import Config
from core.logger import get_logger

logger = get_logger("recipe_manager")

class RecipeManager:
    def __init__(self):
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

    def get_my_recipes(self, user_email: str) -> list[dict]:
        response = self.supabase.table("recipes").select("*") \
            .eq("created_by", user_email) \
            .order("created_at", desc=True).execute()
        return response.data or []

    def get_public_recipes(self, method: str = None) -> list[dict]:
        query = self.supabase.table("recipes").select("*").eq("is_public", True)
        if method:
            query = query.eq("method", method)
        response = query.order("created_at", desc=True).execute()
        return response.data or []

    def get_rag_recipes(self) -> list[dict]:
        response = self.supabase.table("recipes").select("*") \
            .eq("is_public", True) \
            .eq("use_in_rag", True) \
            .order("created_at", desc=True).execute()
        return response.data or []

    def create_recipe(self, recipe: dict) -> dict:
        response = self.supabase.table("recipes").insert(recipe).execute()
        logger.info(f"Receta creada: {recipe.get('name')} por {recipe.get('created_by')}")
        return response.data[0] if response.data else {}

    def make_public(self, recipe_id: str, user_email: str) -> dict:
        response = self.supabase.table("recipes").update({
            "is_public": True,
            "made_public_by": user_email
        }).eq("id", recipe_id).execute()
        logger.info(f"Receta {recipe_id} hecha pública por {user_email}")
        return response.data[0] if response.data else {}

    def make_private(self, recipe_id: str) -> dict:
        response = self.supabase.table("recipes").update({
            "is_public": False,
            "made_public_by": None,
            "use_in_rag": False
        }).eq("id", recipe_id).execute()
        logger.info(f"Receta {recipe_id} hecha privada")
        return response.data[0] if response.data else {}

    def toggle_rag(self, recipe_id: str, use_in_rag: bool) -> dict:
        response = self.supabase.table("recipes").update({
            "use_in_rag": use_in_rag
        }).eq("id", recipe_id).execute()
        logger.info(f"Receta {recipe_id} use_in_rag={use_in_rag}")
        return response.data[0] if response.data else {}

    def delete_recipe(self, recipe_id: str) -> bool:
        self.supabase.table("recipes").delete().eq("id", recipe_id).execute()
        logger.info(f"Receta {recipe_id} eliminada")
        return True

    def search_related_recipes(self, query: str) -> list[dict]:
        recipes = self.get_rag_recipes()
        logger.info(f"search_related_recipes — query: '{query}' | recetas RAG disponibles: {len(recipes)}")
        query_lower = query.lower()
        relevant = []
        for recipe in recipes:
            searchable = " ".join([
                recipe.get("name", ""),
                recipe.get("method", ""),
                recipe.get("coffee_bean", ""),
                recipe.get("flavor_notes", ""),
            ]).lower()
            words = [re.sub(r'[^\w]', '', w) for w in query_lower.split() if len(w) > 2]
            words = [w for w in words if w]
            matches = [w for w in words if w in searchable]
            logger.info(f"  Receta: '{recipe.get('name')}' | searchable: '{searchable}' | words: {words} | matches: {matches}")
            if any(word in searchable for word in words):
                relevant.append(recipe)
        return relevant

    def format_recipe_card(self, recipe: dict) -> str:
        parts = [f"**{recipe.get('name')}** (por {recipe.get('created_by', '').split('@')[0]})"]
        if recipe.get("method"):
            parts.append(f"Método: {recipe['method']}")
        if recipe.get("dose_g") and recipe.get("water_g"):
            parts.append(f"Ratio: {recipe.get('ratio', '-')} · {recipe['dose_g']}g → {recipe['water_g']}g")
        if recipe.get("water_temp_c"):
            parts.append(f"Temperatura: {recipe['water_temp_c']}°C")
        if recipe.get("brew_time_seconds"):
            mins = recipe["brew_time_seconds"] // 60
            secs = recipe["brew_time_seconds"] % 60
            parts.append(f"Tiempo: {mins}:{secs:02d}")
        if recipe.get("flavor_notes"):
            parts.append(f"Notas: {recipe['flavor_notes']}")
        return "\n".join(parts)
