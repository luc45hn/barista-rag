import pytest
import os
from unittest.mock import patch
from core.config import Config

def test_config_has_required_attributes():
    assert hasattr(Config, "SUPABASE_URL")
    assert hasattr(Config, "SUPABASE_KEY")
    assert hasattr(Config, "SUPABASE_SERVICE_KEY")
    assert hasattr(Config, "GOOGLE_API_KEY")
    assert hasattr(Config, "GROQ_API_KEY")
    assert hasattr(Config, "GEMINI_MODEL")
    assert hasattr(Config, "GROQ_MODEL")
    assert hasattr(Config, "EMBEDDING_MODEL")
    assert hasattr(Config, "CHUNK_SIZE")
    assert hasattr(Config, "CHUNK_OVERLAP")
    assert hasattr(Config, "TOP_K_RESULTS")
    assert hasattr(Config, "TEMPERATURE")
    assert hasattr(Config, "MAX_TOKENS")

def test_config_default_values():
    assert Config.CHUNK_SIZE == 1000
    assert Config.CHUNK_OVERLAP == 150
    assert Config.TOP_K_RESULTS == 6
    assert Config.TEMPERATURE == 0.3
    assert Config.MAX_TOKENS == 1024
    assert Config.EMBEDDING_MODEL == "gemini-embedding-001"
    assert Config.GROQ_MODEL == "llama-3.3-70b-versatile"

def test_config_validate_raises_when_missing_supabase():
    with patch.object(Config, "SUPABASE_URL", ""):
        with pytest.raises(ValueError, match="SUPABASE_URL"):
            Config.validate()

def test_config_validate_raises_when_missing_supabase_key():
    with patch.object(Config, "SUPABASE_KEY", ""):
        with pytest.raises(ValueError, match="SUPABASE_KEY"):
            Config.validate()

def test_config_validate_raises_when_missing_both_llm_keys():
    with patch.object(Config, "GOOGLE_API_KEY", ""):
        with patch.object(Config, "GROQ_API_KEY", ""):
            with pytest.raises(ValueError):
                Config.validate()

def test_config_validate_passes_with_groq_only():
    with patch.object(Config, "SUPABASE_URL", "https://test.supabase.co"):
        with patch.object(Config, "SUPABASE_KEY", "test-key"):
            with patch.object(Config, "GOOGLE_API_KEY", ""):
                with patch.object(Config, "GROQ_API_KEY", "test-groq-key"):
                    assert Config.validate() is True
