from types import SimpleNamespace

from agents.reviews import sentiment_analyzer


class FakeCompletions:
    def __init__(self):
        self.last_messages = None

    def create(self, model, messages, temperature):
        self.last_messages = messages
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="sentiment result"))]
        )


class FakeClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=FakeCompletions())


def test_analyze_reviews_uses_first_three_transcripts_and_returns_output(monkeypatch):
    # Arrange
    fake_client = FakeClient()
    monkeypatch.setattr(sentiment_analyzer, "client", fake_client)

    transcripts = [
        "transcript one",
        "transcript two",
        "transcript three",
        "transcript four should be ignored",
    ]

    # Act
    result = sentiment_analyzer.analyze_reviews("Laptop X", transcripts)

    # Assert
    assert result == "sentiment result"
    prompt = fake_client.chat.completions.last_messages[0]["content"]
    assert "transcript one" in prompt
    assert "transcript two" in prompt
    assert "transcript three" in prompt
    assert "transcript four should be ignored" not in prompt
