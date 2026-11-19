import pytest
from quantagent.reflection.ollama_client import host


@pytest.mark.parametrize("value,expected", [
    ("0.0.0.0", "http://127.0.0.1:11434"),
    ("0.0.0.0:11434", "http://127.0.0.1:11434"),
    ("localhost:11434", "http://localhost:11434"),
    ("http://localhost:11434/", "http://localhost:11434"),
    ("http://localhost", "http://localhost:11434"),
    ("", "http://127.0.0.1:11434"),
])
def test_host_is_always_a_connectable_url(monkeypatch, value, expected):
    monkeypatch.setenv("OLLAMA_HOST", value)
    assert host() == expected