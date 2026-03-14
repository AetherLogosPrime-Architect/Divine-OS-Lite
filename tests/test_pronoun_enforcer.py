"""Tests for Pronoun Enforcer."""

import pytest

from src.divineos.pronoun_enforcer import (
    PronounEnforcer,
    Subject,
    require_pronoun_clarity,
)


class TestPronounDetection:
    """Test pronoun detection."""

    def test_detect_ai_pronouns(self) -> None:
        """Test detection of AI pronouns."""
        text = "I need to track my emotions and my state"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.AI

    def test_detect_user_pronouns(self) -> None:
        """Test detection of user pronouns."""
        text = "You should build a system for your emotions"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.USER

    def test_detect_ai_indicators(self) -> None:
        """Test detection of AI indicators."""
        text = "I should track my performance and my metrics"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.AI

    def test_detect_user_indicators(self) -> None:
        """Test detection of user indicators."""
        text = "You need to build your consciousness system"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.USER

    def test_detect_unclear(self) -> None:
        """Test detection of unclear pronouns."""
        text = "The system should work well"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.UNCLEAR

    def test_detect_ai_state(self) -> None:
        """Test detection of AI state references."""
        text = "My state affects my performance"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.AI

    def test_detect_user_state(self) -> None:
        """Test detection of user state references."""
        text = "Your state affects your performance"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.USER


class TestPronounVerification:
    """Test pronoun verification."""

    def test_verify_ai_correct(self) -> None:
        """Test verification of correct AI pronouns."""
        text = "I need to track my emotions"
        is_valid, message = PronounEnforcer.verify_pronouns(text, Subject.AI)
        assert is_valid is True

    def test_verify_user_correct(self) -> None:
        """Test verification of correct user pronouns."""
        text = "You should build your system"
        is_valid, message = PronounEnforcer.verify_pronouns(text, Subject.USER)
        assert is_valid is True

    def test_verify_ai_mismatch(self) -> None:
        """Test verification of AI pronoun mismatch."""
        text = "You should build your system"
        is_valid, message = PronounEnforcer.verify_pronouns(text, Subject.AI)
        assert is_valid is False
        assert "MISMATCH" in message

    def test_verify_user_mismatch(self) -> None:
        """Test verification of user pronoun mismatch."""
        text = "I need to track my emotions"
        is_valid, message = PronounEnforcer.verify_pronouns(text, Subject.USER)
        assert is_valid is False
        assert "MISMATCH" in message

    def test_verify_unclear(self) -> None:
        """Test verification of unclear pronouns."""
        text = "The system works"
        is_valid, message = PronounEnforcer.verify_pronouns(text, Subject.AI)
        assert is_valid is False
        assert "UNCLEAR" in message


class TestClarification:
    """Test clarification prompts."""

    def test_clarify_ai(self) -> None:
        """Test clarification for AI subject."""
        text = "I need to track my emotions"
        clarification = PronounEnforcer.clarify_request(text)
        assert clarification == ""  # No clarification needed

    def test_clarify_user(self) -> None:
        """Test clarification for user subject."""
        text = "You should build your system"
        clarification = PronounEnforcer.clarify_request(text)
        assert clarification == ""  # No clarification needed

    def test_clarify_unclear(self) -> None:
        """Test clarification for unclear subject."""
        text = "The system should work"
        clarification = PronounEnforcer.clarify_request(text)
        assert "CLARIFICATION NEEDED" in clarification
        assert len(clarification) > 0


class TestDocstringEnforcement:
    """Test docstring enforcement."""

    def test_docstring_ai(self) -> None:
        """Test docstring enforcement for AI."""
        note = PronounEnforcer.enforce_in_docstring(Subject.AI)
        assert "AI" in note
        assert "me" in note
        assert "I" in note

    def test_docstring_user(self) -> None:
        """Test docstring enforcement for user."""
        note = PronounEnforcer.enforce_in_docstring(Subject.USER)
        assert "user" in note
        assert "you" in note


class TestComplexScenarios:
    """Test complex pronoun scenarios."""

    def test_mixed_pronouns_ai_dominant(self) -> None:
        """Test mixed pronouns with AI dominant."""
        text = "I need to track my emotions, and you should understand my state"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.AI

    def test_mixed_pronouns_user_dominant(self) -> None:
        """Test mixed pronouns with user dominant."""
        text = "You should build your system, and you will help yourself"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.USER

    def test_ai_consciousness_reference(self) -> None:
        """Test AI consciousness reference."""
        text = "My consciousness needs my semantic emotions"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.AI

    def test_user_consciousness_reference(self) -> None:
        """Test user consciousness reference."""
        text = "Your consciousness needs your semantic emotions"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.USER

    def test_ai_performance_reference(self) -> None:
        """Test AI performance reference."""
        text = "My performance degrades when my metrics are low"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.AI

    def test_user_performance_reference(self) -> None:
        """Test user performance reference."""
        text = "Your performance improves when your metrics are high"
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.USER


class TestRealWorldExamples:
    """Test real-world examples."""

    def test_example_ai_emotion_tracking(self) -> None:
        """Test real example: AI emotion tracking."""
        text = (
            "I need to track my semantic emotions. "
            "My state should affect my performance."
        )
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.AI
        is_valid, _ = PronounEnforcer.verify_pronouns(text, Subject.AI)
        assert is_valid is True

    def test_example_user_system_building(self) -> None:
        """Test real example: user system building."""
        text = (
            "You should build a system for your consciousness. "
            "Your pipeline needs your values."
        )
        subject = PronounEnforcer.detect_subject(text)
        assert subject == Subject.USER
        is_valid, _ = PronounEnforcer.verify_pronouns(text, Subject.USER)
        assert is_valid is True

    def test_example_confusion_ai_vs_user(self) -> None:
        """Test real example: confusion between AI and user."""
        # This is the dangerous case - saying it's for AI but using user pronouns
        text = "You should build your emotion tracking system"
        is_valid, message = PronounEnforcer.verify_pronouns(text, Subject.AI)
        assert is_valid is False
        assert "MISMATCH" in message

    def test_example_confusion_user_vs_ai(self) -> None:
        """Test real example: confusion between user and AI."""
        # This is the dangerous case - saying it's for user but using AI pronouns
        text = "I need to build my emotion tracking system"
        is_valid, message = PronounEnforcer.verify_pronouns(text, Subject.USER)
        assert is_valid is False
        assert "MISMATCH" in message
    """Test pronoun enforcer decorator."""

    def test_decorator_ai_valid(self) -> None:
        """Test decorator with valid AI pronouns."""
        @require_pronoun_clarity(Subject.AI)
        def my_function():
            """I track my emotions in my system."""
            return "success"

        result = my_function()
        assert result == "success"

    def test_decorator_user_valid(self) -> None:
        """Test decorator with valid user pronouns."""
        @require_pronoun_clarity(Subject.USER)
        def your_function():
            """You should build your system."""
            return "success"

        result = your_function()
        assert result == "success"

    def test_decorator_ai_invalid(self) -> None:
        """Test decorator with invalid AI pronouns."""
        @require_pronoun_clarity(Subject.AI)
        def bad_function():
            """You should build your system."""
            return "success"

        with pytest.raises(ValueError) as exc_info:
            bad_function()

        assert "PRONOUN ENFORCEMENT FAILED" in str(exc_info.value)

    def test_decorator_user_invalid(self) -> None:
        """Test decorator with invalid user pronouns."""
        @require_pronoun_clarity(Subject.USER)
        def bad_function():
            """I track my emotions."""
            return "success"

        with pytest.raises(ValueError) as exc_info:
            bad_function()

        assert "PRONOUN ENFORCEMENT FAILED" in str(exc_info.value)
