from supabase import create_client
from core.config import Config
from core.logger import get_logger

logger = get_logger("recipe_manager")

class RecipeManager:
    def __init__(self):
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    def get_approved_recipes(self, method: str = None, all_users: bool = True) -> list[dict]:
        query = self.supabase.table("recipes").select("*").eq("approved", True)
        if method:
            query = query.eq("method", method)
        response = query.order("created_at", desc=True).execute()
        return response.data or []

    def get_pending_recipes(self, created_by: str = None) -> list[dict]:
        query = self.supabase.table("recipes").select("*").eq("approved", False)
        if created_by:
            query = query.eq("created_by", created_by)
        response = query.order("created_at", desc=True).execute()
        return response.data or []

    def create_recipe(self, recipe: dict) -> dict:
        response = self.supabase.table("recipes").insert(recipe).execute()
        logger.info(f"Receta creada: {recipe.get('name')} por {recipe.get('created_by')}")
        return response.data[0] if response.data else {}

    def approve_recipe(self, recipe_id: str, approved_by: str) -> dict:
        response = self.supabase.table("recipes").update({
            "approved": True,
            "approved_by": approved_by
        }).eq("id", recipe_id).execute()
        logger.info(f"Receta {recipe_id} aprobada por {approved_by}")
        return response.data[0] if response.data else {}

    def delete_recipe(self, recipe_id: str) -> bool:
        self.supabase.table("recipes").delete().eq("id", recipe_id).execute()
        logger.info(f"Receta {recipe_id} eliminada")
        return True

    def format_recipes_context(self, recipes: list[dict]) -> str:
        if not recipes:
            return ""

        context_parts = []
        for r in recipes:
            parts = [f"**Receta propia: {r.get('name')}**"]
            if r.get("coffee_bean"):
                parts.append(f"Café: {r['coffee_bean']}")
            if r.get("method"):
                parts.append(f"Método: {r['method']}")
            if r.get("dose_g"):
                parts.append(f"Dosis: {r['dose_g']}g")
            if r.get("water_g"):
                parts.append(f"Agua: {r['water_g']}g")
            if r.get("ratio"):
                parts.append(f"Ratio: {r['ratio']}")
            if r.get("water_temp_c"):
                parts.append(f"Temperatura: {r['water_temp_c']}°C")
            if r.get("brew_time_seconds"):
                mins = r["brew_time_seconds"] // 60
                secs = r["brew_time_seconds"] % 60
                parts.append(f"Tiempo: {mins}:{secs:02d} min")
            if r.get("yield_g"):
                parts.append(f"Rendimiento: {r['yield_g']}g")
            if r.get("grind_notes"):
                parts.append(f"Molienda: {r['grind_notes']}")
            if r.get("flavor_notes"):
                parts.append(f"Notas de sabor: {r['flavor_notes']}")
            if r.get("tips"):
                parts.append(f"Tips: {r['tips']}")
            context_parts.append("\n".join(parts))

        return "\n\n".join(context_parts)

    def search_recipes(self, query: str) -> list[dict]:
        query_lower = query.lower()
        recipes = self.get_approved_recipes(all_users=True)
        relevant = []
        for recipe in recipes:
            searchable = " ".join([
                recipe.get("name", ""),
                recipe.get("method", ""),
                recipe.get("coffee_bean", ""),
                recipe.get("flavor_notes", ""),
            ]).lower()
            if any(word in searchable for word in query_lower.split()):
                relevant.append(recipe)
        return relevant
