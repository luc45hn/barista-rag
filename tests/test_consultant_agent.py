import pytest
from unittest.mock import MagicMock, patch
from core.consultant_agent import ConsultantAgent, detect_intent

def test_detect_intent_recipe():
    intents = detect_intent("¿cómo preparo el V60?")
    assert "recipe" in intents

def test_detect_intent_troubleshoot():
    intents = detect_intent("mi espresso sale muy ácido")
    assert "troubleshoot" in intents

def test_detect_intent_origin():
    intents = detect_intent("¿qué café de Etiopía me recomendás?")
    assert "origin" in intents

def test_detect_intent_sensory():
    intents = detect_intent("¿qué notas de sabor tiene este café?")
    assert "sensory" in intents

def test_detect_intent_multiple():
    intents = detect_intent("el espresso de Etiopía me sale ácido")
    assert "troubleshoot" in intents
    assert "origin" in intents

def test_detect_intent_general_fallback():
    intents = detect_intent("hola cómo estás")
    assert intents == ["general"]

def test_detect_intent_case_insensitive():
    intents = detect_intent("ESPRESSO TEMPERATURA")
    assert "recipe" in intents

@pytest.fixture
def mock_agent():
    with patch("core.consultant_agent.DocumentManager") as mock_dm, \
         patch("core.consultant_agent.RecipeManager") as mock_rm, \
         patch("core.consultant_agent.genai.Client"), \
         patch("core.consultant_agent.create_client") as mock_supabase:
        agent = ConsultantAgent(gemini_api_key="test-key")
        agent.document_manager = MagicMock()
        agent.recipe_manager = MagicMock()
        agent.groq_client = MagicMock()
        agent.genai_client = MagicMock()
        agent.supabase = MagicMock()
        # Mockear _generate para evitar llamadas reales
        agent._generate = MagicMock(return_value=("Respuesta de prueba.", "groq"))
        yield agent

def test_chat_returns_answer_and_sources(mock_agent):
    mock_agent.document_manager.search.return_value = [
        {"content": "El espresso requiere 9 bar", "metadata": {"source": "04_espresso_fundamentos.md"}, "similarity": 0.85}
    ]
    mock_agent.document_manager.format_context.return_value = "El espresso requiere 9 bar"
    mock_agent.recipe_manager.search_related_recipes.return_value = []
    answer, sources, related_recipes = mock_agent.chat("¿cuánta presión necesita el espresso?")
    assert isinstance(answer, str)
    assert len(answer) > 0
    assert isinstance(sources, list)
    assert isinstance(related_recipes, list)

def test_chat_returns_related_recipes(mock_agent):
    own_recipe = {"name": "V60 Etiopía", "method": "v60", "dose_g": 15, "water_g": 240}
    mock_agent.recipe_manager.search_related_recipes.return_value = [own_recipe]
    mock_agent.document_manager.search.return_value = []
    mock_agent.document_manager.format_context.return_value = ""
    answer, sources, related_recipes = mock_agent.chat("cómo preparo el V60")
    assert len(related_recipes) == 1
    assert related_recipes[0]["name"] == "V60 Etiopía"

def test_chat_with_history(mock_agent):
    mock_agent.document_manager.search.return_value = []
    mock_agent.document_manager.format_context.return_value = ""
    mock_agent.recipe_manager.search_related_recipes.return_value = []
    history = [
        {"role": "user", "content": "Hola"},
        {"role": "assistant", "content": "Hola, soy Barista IA"},
    ]
    answer, sources, related_recipes = mock_agent.chat("¿y el cappuccino?", history=history)
    assert isinstance(answer, str)
    assert len(answer) > 0

def test_chat_empty_context_still_responds(mock_agent):
    mock_agent.document_manager.search.return_value = []
    mock_agent.document_manager.format_context.return_value = ""
    mock_agent.recipe_manager.search_related_recipes.return_value = []
    answer, sources, related_recipes = mock_agent.chat("pregunta muy específica sin contexto")
    assert isinstance(answer, str)
    assert sources == []
    assert related_recipes == []

def test_build_context_returns_four_values(mock_agent):
    mock_agent.recipe_manager.search_related_recipes.return_value = [
        {"name": "Espresso", "method": "espresso", "dose_g": 18}
    ]
    mock_agent.document_manager.search.return_value = [
        {"content": "El espresso tiene 9 bar", "metadata": {"source": "04_espresso_fundamentos.md"}}
    ]
    mock_agent.document_manager.format_context.return_value = "El espresso tiene 9 bar"
    context, sources, intents, related_recipes = mock_agent.build_context("espresso")
    assert isinstance(context, str)
    assert isinstance(sources, list)
    assert isinstance(intents, list)
    assert isinstance(related_recipes, list)
    assert len(related_recipes) == 1

def test_chat_passes_cafe_id_to_build_context(mock_agent):
    mock_agent.document_manager.search.return_value = []
    mock_agent.document_manager.format_context.return_value = ""
    mock_agent.recipe_manager.search_related_recipes.return_value = []
    mock_agent.chat("como preparo un V60", cafe_id="7bdb4c89-8806-478d-9446-a80135c894bf")
    call_args = mock_agent.recipe_manager.search_related_recipes.call_args
    assert call_args[1].get("cafe_id") == "7bdb4c89-8806-478d-9446-a80135c894bf"

def test_build_context_passes_cafe_id_to_search(mock_agent):
    mock_agent.recipe_manager.search_related_recipes.return_value = []
    mock_agent.document_manager.search.return_value = []
    mock_agent.document_manager.format_context.return_value = ""
    mock_agent.build_context("espresso", cafe_id="7bdb4c89-8806-478d-9446-a80135c894bf")
    call_args = mock_agent.recipe_manager.search_related_recipes.call_args
    assert call_args[1].get("cafe_id") == "7bdb4c89-8806-478d-9446-a80135c894bf"
