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
    "approved": True,
    "approved_by": "ana@barista.com",
    "created_at": "2026-01-01T10:00:00Z",
}

def test_get_approved_recipes_filters_approved(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.get_approved_recipes()
    mock_recipe_manager.supabase.table.assert_called_with("recipes")
    assert len(results) == 1

def test_get_approved_recipes_returns_empty_list_on_none(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.order.return_value.execute.return_value = MagicMock(data=None)
    results = mock_recipe_manager.get_approved_recipes()
    assert results == []

def test_get_pending_recipes(mock_recipe_manager):
    pending = {**SAMPLE_RECIPE, "approved": False, "approved_by": None}
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.order.return_value.execute.return_value = MagicMock(data=[pending])
    results = mock_recipe_manager.get_pending_recipes()
    assert len(results) == 1

def test_create_recipe_calls_insert(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.insert.return_value \
        .execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    result = mock_recipe_manager.create_recipe(SAMPLE_RECIPE)
    mock_recipe_manager.supabase.table.assert_called_with("recipes")
    assert result == SAMPLE_RECIPE

def test_create_recipe_returns_empty_on_failure(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.insert.return_value \
        .execute.return_value = MagicMock(data=None)
    result = mock_recipe_manager.create_recipe(SAMPLE_RECIPE)
    assert result == {}

def test_approve_recipe(mock_recipe_manager):
    approved = {**SAMPLE_RECIPE, "approved": True, "approved_by": "ana@barista.com"}
    mock_recipe_manager.supabase.table.return_value.update.return_value \
        .eq.return_value.execute.return_value = MagicMock(data=[approved])
    result = mock_recipe_manager.approve_recipe("abc-123", "ana@barista.com")
    assert result["approved"] is True
    assert result["approved_by"] == "ana@barista.com"

def test_delete_recipe(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.delete.return_value \
        .eq.return_value.execute.return_value = MagicMock()
    result = mock_recipe_manager.delete_recipe("abc-123")
    assert result is True

def test_search_recipes_finds_by_method(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.search_recipes("v60")
    assert len(results) == 1

def test_search_recipes_finds_by_flavor_notes(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.search_recipes("jazmín")
    assert len(results) == 1

def test_search_recipes_returns_empty_on_no_match(mock_recipe_manager):
    mock_recipe_manager.supabase.table.return_value.select.return_value \
        .eq.return_value.order.return_value.execute.return_value = MagicMock(data=[SAMPLE_RECIPE])
    results = mock_recipe_manager.search_recipes("siphon")
    assert results == []

def test_format_recipes_context_empty(mock_recipe_manager):
    result = mock_recipe_manager.format_recipes_context([])
    assert result == ""

def test_format_recipes_context_includes_name(mock_recipe_manager):
    result = mock_recipe_manager.format_recipes_context([SAMPLE_RECIPE])
    assert "V60 Etiopía" in result

def test_format_recipes_context_includes_parameters(mock_recipe_manager):
    result = mock_recipe_manager.format_recipes_context([SAMPLE_RECIPE])
    assert "15.0" in result or "15" in result
    assert "93.0" in result or "93" in result
    assert "Jazmín" in result
