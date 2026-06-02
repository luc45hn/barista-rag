import pytest
from unittest.mock import MagicMock, patch
from core.recipe_manager import RecipeManager

@pytest.fixture
def mock_recipe_manager():
    with patch("core.recipe_manager.create_client"):
        manager = RecipeManager()
        manager.supabase = MagicMock()
        yield manager

SAMPLE_RECIPE = {
    "id": "abc-123",
    "cafe_name": "Barista IA",
    "name": "V60 Etiopía",
    "method": "v60",
    "coffee_bean": "Etiopía Yirgacheffe",
    "dose_g": 15.0,
    "water_g": 240.0,
    "ratio": "1:16",
    "water_temp_c": 93.0,
    "brew_time_seconds": 210,
    "yield_g": None,
    "grind_notes": "Ajuste 14",
    "flavor_notes": "Jazmín, limón",
    "tips": "Enjuagar filtro",
    "created_by": "maria@barista.com",
    "is_public": True,
    "made_public_by": "maria@barista.com",
    "use_in_rag": True,
    "created_at": "2026-01-01T10:00:00Z",
}

def test_get_public_recipes(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.get_public_recipes()
    assert len(results) == 1

def test_get_public_recipes_returns_empty_on_none(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.order.return_value.execute.return_value = MagicMock(data=None)
    results = mock_recipe_manager.get_public_recipes()
    assert results == []

def test_get_my_recipes(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.get_my_recipes("maria@barista.com")
    assert len(results) == 1

def test_get_rag_recipes(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.get_rag_recipes()
    assert len(results) == 1

def test_create_recipe_calls_insert(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.insert.return_value \
        .execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    result = mock_recipe_manager.create_recipe(SAMPLE_RECIPE)
    assert result == SAMPLE_RECIPE

def test_create_recipe_returns_empty_on_failure(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.insert.return_value \
        .execute.return_value = MagicMock(data=None)
    result = mock_recipe_manager.create_recipe(SAMPLE_RECIPE)
    assert result == {}

def test_make_public(mock_recipe_manager):
    public = {**SAMPLE_RECIPE, "is_public": True, "made_public_by": "maria@barista.com"}
    mock_recipe_manager.supabase.table.return_value.update.return_value \
        .eq.return_value.execute.return_value = MagicMock(data=[public])
    result = mock_recipe_manager.make_public("abc-123", "maria@barista.com")
    assert result["is_public"] is True

def test_make_private(mock_recipe_manager):
    private = {**SAMPLE_RECIPE, "is_public": False, "use_in_rag": False}
    mock_recipe_manager.supabase.table.return_value.update.return_value \
        .eq.return_value.execute.return_value = MagicMock(data=[private])
    result = mock_recipe_manager.make_private("abc-123")
    assert result["is_public"] is False

def test_toggle_rag(mock_recipe_manager):
    updated = {**SAMPLE_RECIPE, "use_in_rag": True}
    mock_recipe_manager.supabase.table.return_value.update.return_value \
        .eq.return_value.execute.return_value = MagicMock(data=[updated])
    result = mock_recipe_manager.toggle_rag("abc-123", True)
    assert result["use_in_rag"] is True

def test_delete_recipe(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.delete.return_value \
        .eq.return_value.execute.return_value = MagicMock()
    result = mock_recipe_manager.delete_recipe("abc-123")
    assert result is True

def test_search_related_recipes_finds_by_method(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.search_related_recipes("v60")
    assert len(results) == 1

def test_search_related_recipes_finds_by_flavor_notes(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.search_related_recipes("jazmín")
    assert len(results) == 1

def test_search_related_recipes_returns_empty_on_no_match(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.search_related_recipes("siphon")
    assert results == []

def test_format_recipe_card_empty(mock_recipe_manager):
    result = mock_recipe_manager.format_recipe_card({})
    assert isinstance(result, str)

def test_format_recipe_card_includes_name(mock_recipe_manager):
    result = mock_recipe_manager.format_recipe_card(SAMPLE_RECIPE)
    assert "V60 Etiopía" in result

def test_format_recipe_card_includes_parameters(mock_recipe_manager):
    result = mock_recipe_manager.format_recipe_card(SAMPLE_RECIPE)
    assert "15" in result or "15.0" in result
    assert "93" in result or "93.0" in result

def test_get_public_recipes_filters_by_cafe_id(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.get_public_recipes(cafe_id="7bdb4c89-8806-478d-9446-a80135c894bf")
    assert len(results) == 1

def test_get_rag_recipes_filters_by_cafe_id(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.get_rag_recipes(cafe_id="7bdb4c89-8806-478d-9446-a80135c894bf")
    assert len(results) == 1

def test_search_related_recipes_with_cafe_id(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.search_related_recipes("v60", cafe_id="7bdb4c89-8806-478d-9446-a80135c894bf")
    assert len(results) == 1

def test_search_related_recipes_no_cafe_id_returns_all(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.search_related_recipes("v60")
    assert isinstance(results, list)
