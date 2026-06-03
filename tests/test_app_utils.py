import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Importamos las funciones directamente
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_load_messages_returns_list_on_success():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value \
        .eq.return_value.order.return_value.limit.return_value \
        .execute.return_value = MagicMock(data=[
            {"role": "user", "content": "Hola", "sources": [], "related_recipes": []},
            {"role": "assistant", "content": "Hola! Soy Barista IA", "sources": [], "related_recipes": []},
        ])

    from app import load_messages_from_db
    result = load_messages_from_db(mock_supabase, "test@example.com")
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "assistant"

def test_load_messages_returns_empty_on_error():
    mock_supabase = MagicMock()
    mock_supabase.table.side_effect = Exception("DB error")

    from app import load_messages_from_db
    result = load_messages_from_db(mock_supabase, "test@example.com")
    assert result == []

def test_load_messages_returns_empty_on_none_data():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value \
        .eq.return_value.order.return_value.limit.return_value \
        .execute.return_value = MagicMock(data=None)

    from app import load_messages_from_db
    result = load_messages_from_db(mock_supabase, "test@example.com")
    assert result == []

def test_save_message_calls_insert():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.insert.return_value \
        .execute.return_value = MagicMock()

    from app import save_message_to_db
    save_message_to_db(
        mock_supabase,
        "test@example.com",
        "cafe-uuid",
        "user",
        "Como preparo un V60?",
        sources=[],
        related_recipes=[]
    )
    mock_supabase.table.assert_called_with("messages")
    mock_supabase.table.return_value.insert.assert_called_once()

def test_save_message_handles_error_silently():
    mock_supabase = MagicMock()
    mock_supabase.table.side_effect = Exception("DB error")

    from app import save_message_to_db
    # No debe lanzar excepción
    save_message_to_db(mock_supabase, "test@example.com", "", "user", "test")

def test_save_message_inserts_correct_fields():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.insert.return_value \
        .execute.return_value = MagicMock()

    from app import save_message_to_db
    save_message_to_db(
        mock_supabase,
        "maria@barista.com",
        "cafe-123",
        "assistant",
        "El ratio del V60 es 1:16",
        sources=["04_espresso_fundamentos.md"],
        related_recipes=[{"name": "V60 Kenia"}]
    )
    call_args = mock_supabase.table.return_value.insert.call_args[0][0]
    assert call_args["user_email"] == "maria@barista.com"
    assert call_args["cafe_id"] == "cafe-123"
    assert call_args["role"] == "assistant"
    assert call_args["content"] == "El ratio del V60 es 1:16"
    assert call_args["sources"] == ["04_espresso_fundamentos.md"]

def test_format_sources_replaces_filenames():
    from app import format_sources
    result = format_sources(["04_espresso_fundamentos.md", "10_james_hoffmann_tecnicas.md"])
    assert "Espresso Fundamentos" in result
    assert "James Hoffmann" in result

def test_format_sources_handles_unknown_source():
    from app import format_sources
    result = format_sources(["unknown_doc.md"])
    assert "unknown_doc.md" in result

def test_format_sources_empty():
    from app import format_sources
    result = format_sources([])
    assert result == ""
