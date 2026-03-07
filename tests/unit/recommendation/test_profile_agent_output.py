import pytest
from pydantic import ValidationError

from agents.profile.schemas import ProfileAgentOutput, UserProfile


def test_profile_agent_output_handles_complete_and_partial_profiles():
    # Arrange
    complete_payload = {
        "profile": {
            "product_category": "laptop",
            "product_intent": "gaming",
            "budget": "30000-50000",
            "country": "Egypt",
            "preferences": {"brand": "Lenovo"},
            "search_queries": ["gaming laptop"],
        },
        "missing_fields": [],
        "is_complete": True,
        "next_question": None,
    }

    partial_payload = {
        "profile": {
            "product_category": "laptop",
            "product_intent": None,
            "budget": None,
            "country": "Egypt",
            "preferences": {},
            "search_queries": [],
        },
        "missing_fields": ["product_intent", "budget"],
        "is_complete": False,
        "next_question": "What is your budget range?",
    }

    # Act
    complete_output = ProfileAgentOutput.model_validate(complete_payload)
    partial_output = ProfileAgentOutput.model_validate(partial_payload)

    # Assert
    assert isinstance(complete_output.profile, UserProfile)
    assert complete_output.is_complete is True
    assert complete_output.missing_fields == []

    assert isinstance(partial_output.profile, UserProfile)
    assert partial_output.is_complete is False
    assert partial_output.missing_fields == ["product_intent", "budget"]


def test_profile_agent_output_rejects_missing_fields_key():
    # Arrange
    payload = {
        "profile": {
            "product_category": "laptop",
            "product_intent": "gaming",
            "budget": "30000-50000",
            "country": "Egypt",
            "preferences": {},
            "search_queries": ["gaming laptop"],
        },
        "is_complete": True,
    }

    # Act / Assert
    with pytest.raises(ValidationError):
        ProfileAgentOutput.model_validate(payload)
