import pytest
from unittest.mock import MagicMock, patch
from core.document_manager import DocumentManager

@pytest.fixture
def mock_document_manager():
    with patch("core.document_manager.create_client") as mock_supabase, \
         patch("core.document_manager.genai.Client") as mock_genai:
        manager = DocumentManager()
        manager.supabase = MagicMock()
        manager.genai_client = MagicMock()
        yield manager

def test_get_embedding_returns_list(mock_document_manager):
    mock_document_manager.genai_client.models.embed_content.return_value = MagicMock(
        embeddings=[MagicMock(values=[0.1, 0.2, 0.3] * 256)]
    )
    result = mock_document_manager.get_embedding("test query")
    assert isinstance(result, list)
    assert len(result) == 768

def test_search_calls_rpc(mock_document_manager):
    mock_document_manager.genai_client.models.embed_content.return_value = MagicMock(
        embeddings=[MagicMock(values=[0.1] * 768)]
    )
    mock_document_manager.supabase.rpc.return_value.execute.return_value = MagicMock(
        data=[
            {"id": 1, "content": "El espresso requiere 9 bar de presión", "metadata": {"source": "04_espresso_fundamentos.md"}, "similarity": 0.85},
            {"id": 2, "content": "Temperatura ideal 93°C", "metadata": {"source": "04_espresso_fundamentos.md"}, "similarity": 0.80},
        ]
    )
    results = mock_document_manager.search("espresso temperatura")
    mock_document_manager.supabase.rpc.assert_called_once_with(
        "match_documents",
        {"query_embedding": [0.1] * 768, "match_count": 6}
    )
    assert len(results) == 2

def test_search_returns_empty_on_no_results(mock_document_manager):
    mock_document_manager.genai_client.models.embed_content.return_value = MagicMock(
        embeddings=[MagicMock(values=[0.1] * 768)]
    )
    mock_document_manager.supabase.rpc.return_value.execute.return_value = MagicMock(data=[])
    results = mock_document_manager.search("consulta sin resultados")
    assert results == []

def test_format_context_empty_results(mock_document_manager):
    result = mock_document_manager.format_context([])
    assert result == ""

def test_format_context_includes_source(mock_document_manager):
    docs = [{"content": "Texto de prueba", "metadata": {"source": "04_espresso_fundamentos.md"}}]
    result = mock_document_manager.format_context(docs)
    assert "04_espresso_fundamentos.md" in result
    assert "Texto de prueba" in result

def test_format_context_separates_multiple_docs(mock_document_manager):
    docs = [
        {"content": "Chunk uno", "metadata": {"source": "doc1.md"}},
        {"content": "Chunk dos", "metadata": {"source": "doc2.md"}},
    ]
    result = mock_document_manager.format_context(docs)
    assert "Chunk uno" in result
    assert "Chunk dos" in result
    assert "---" in result

def test_search_uses_top_k_config(mock_document_manager):
    mock_document_manager.genai_client.models.embed_content.return_value = MagicMock(
        embeddings=[MagicMock(values=[0.1] * 768)]
    )
    mock_document_manager.supabase.rpc.return_value.execute.return_value = MagicMock(data=[])
    mock_document_manager.search("query", top_k=6)
    call_args = mock_document_manager.supabase.rpc.call_args
    assert call_args[0][1]["match_count"] == 6
