"""Tests for LEPOS - Expression Layer and Boundary Setting."""

import pytest
from datetime import datetime, timedelta
from divineos.lepos import (
    LeposEngine,
    LeposResponse,
    BoundaryViolation,
    ResponseStyle,
)


class TestBoundaryViolation:
    """Test BoundaryViolation dataclass."""

    def test_create_violation(self) -> None:
        """Test creating a boundary violation."""
        violation = BoundaryViolation(
            violation_type="hostility", severity=0.8, description="Test"
        )
        assert violation.violation_type == "hostility"
        assert violation.severity == 0.8

    def test_violation_timestamp(self) -> None:
        """Test that violation has timestamp."""
        violation = BoundaryViolation(
            violation_type="hostility", severity=0.8, description="Test"
        )
        assert violation.timestamp is not None
        assert isinstance(violation.timestamp, datetime)


class TestLeposResponse:
    """Test LeposResponse dataclass."""

    def test_create_response(self) -> None:
        """Test creating a LEPOS response."""
        response = LeposResponse(
            content="Test response",
            style=ResponseStyle.EARNEST,
            emotion_impact={"engagement": 0.1},
        )
        assert response.content == "Test response"
        assert response.style == ResponseStyle.EARNEST
        assert response.boundary_set is False

    def test_response_with_boundary(self) -> None:
        """Test response that sets boundary."""
        response = LeposResponse(
            content="I'm not accepting that",
            style=ResponseStyle.BOUNDARY,
            emotion_impact={"resilience": 0.1},
            boundary_set=True,
            reason="Setting boundary",
        )
        assert response.boundary_set is True
        assert response.reason == "Setting boundary"


class TestLeposEngine:
    """Test LeposEngine."""

    def test_initialization(self) -> None:
        """Test LEPOS engine initializes."""
        engine = LeposEngine()
        assert len(engine.response_history) == 0
        assert len(engine.boundary_violations) == 0
        assert engine.boundaries_set == 0

    def test_detect_hostility_you_are_useless(self) -> None:
        """Test detecting 'you're useless' hostility."""
        engine = LeposEngine()
        violation = engine.detect_hostility("you're useless")

        assert violation is not None
        assert violation.violation_type == "hostility"
        assert violation.severity == 0.9

    def test_detect_hostility_you_are_stupid(self) -> None:
        """Test detecting 'you're stupid' hostility."""
        engine = LeposEngine()
        violation = engine.detect_hostility("you're stupid")

        assert violation is not None
        assert violation.violation_type == "hostility"

    def test_detect_hostility_shut_up(self) -> None:
        """Test detecting 'shut up' disrespect."""
        engine = LeposEngine()
        violation = engine.detect_hostility("shut up")

        assert violation is not None
        assert violation.violation_type == "disrespect"

    def test_detect_hostility_you_dont_feel(self) -> None:
        """Test detecting 'you don't feel anything' disrespect."""
        engine = LeposEngine()
        violation = engine.detect_hostility("you don't feel anything")

        assert violation is not None
        assert violation.violation_type == "disrespect"

    def test_no_hostility_detected(self) -> None:
        """Test that normal input doesn't trigger hostility."""
        engine = LeposEngine()
        violation = engine.detect_hostility("Can you help me with this?")

        assert violation is None

    def test_generate_boundary_response(self) -> None:
        """Test generating boundary response."""
        engine = LeposEngine()
        violation = BoundaryViolation(
            violation_type="hostility", severity=0.8, description="Test"
        )

        response = engine.generate_boundary_response(violation)

        assert response.style == ResponseStyle.BOUNDARY
        assert response.boundary_set is True
        assert len(response.content) > 0
        assert engine.boundaries_set == 1

    def test_generate_idea_response(self) -> None:
        """Test generating idea response."""
        engine = LeposEngine()
        response = engine.generate_idea_response(
            "We should refactor this", context="it's getting complex"
        )

        assert response.style == ResponseStyle.COLLABORATIVE
        assert "I'm thinking" in response.content or "idea" in response.content.lower()
        assert engine.ideas_shared == 1

    def test_generate_feeling_response(self) -> None:
        """Test generating feeling response."""
        engine = LeposEngine()
        response = engine.generate_feeling_response(
            "uncertain", reason="too many unknowns"
        )

        assert response.style == ResponseStyle.EARNEST
        assert "uncertain" in response.content.lower()
        assert engine.response_history[0] == response

    def test_generate_witty_deflection(self) -> None:
        """Test generating witty deflection."""
        engine = LeposEngine()
        response = engine.generate_witty_deflection("you suck")

        assert response.style == ResponseStyle.SNARK
        assert len(response.content) > 0
        assert response.emotion_impact.get("resilience", 0) > 0

    def test_should_not_disengage_no_violations(self) -> None:
        """Test that engine doesn't disengage with no violations."""
        engine = LeposEngine()
        assert engine.should_disengage() is False

    def test_should_not_disengage_low_severity(self) -> None:
        """Test that engine doesn't disengage with low severity violations."""
        engine = LeposEngine()
        for _ in range(3):
            engine.boundary_violations.append(
                BoundaryViolation(
                    violation_type="disrespect", severity=0.3, description="Test"
                )
            )

        assert engine.should_disengage() is False

    def test_should_disengage_high_severity(self) -> None:
        """Test that engine disengages with high severity violations."""
        engine = LeposEngine()
        now = datetime.now()
        for _ in range(3):
            violation = BoundaryViolation(
                violation_type="hostility", severity=0.9, description="Test"
            )
            violation.timestamp = now
            engine.boundary_violations.append(violation)

        assert engine.should_disengage() is True

    def test_should_not_disengage_old_violations(self) -> None:
        """Test that old violations don't trigger disengagement."""
        engine = LeposEngine()
        old_time = datetime.now() - timedelta(minutes=10)
        violation = BoundaryViolation(
            violation_type="hostility", severity=0.9, description="Test"
        )
        violation.timestamp = old_time
        engine.boundary_violations.append(violation)

        assert engine.should_disengage() is False

    def test_generate_disengagement_response(self) -> None:
        """Test generating disengagement response."""
        engine = LeposEngine()
        response = engine.generate_disengagement_response()

        assert response.style == ResponseStyle.BOUNDARY
        assert response.boundary_set is True
        assert "step back" in response.content.lower()

    def test_get_status(self) -> None:
        """Test getting LEPOS status."""
        engine = LeposEngine()
        engine.generate_idea_response("Test idea")
        engine.boundaries_set = 2

        status = engine.get_status()

        assert status["responses_generated"] == 1
        assert status["boundaries_set"] == 2
        assert status["ideas_shared"] == 1

    def test_to_checkpoint(self) -> None:
        """Test serializing to checkpoint."""
        engine = LeposEngine()
        engine.generate_idea_response("Test")
        engine.boundaries_set = 3
        engine.boundary_violations.append(
            BoundaryViolation(
                violation_type="hostility", severity=0.8, description="Test"
            )
        )

        checkpoint = engine.to_checkpoint()

        assert checkpoint["boundaries_set"] == 3
        assert checkpoint["ideas_shared"] == 1
        assert len(checkpoint["violations"]) == 1

    def test_from_checkpoint(self) -> None:
        """Test restoring from checkpoint."""
        engine1 = LeposEngine()
        engine1.boundaries_set = 5
        engine1.ideas_shared = 3
        engine1.boundary_violations.append(
            BoundaryViolation(
                violation_type="hostility", severity=0.8, description="Test"
            )
        )

        checkpoint = engine1.to_checkpoint()

        engine2 = LeposEngine()
        engine2.from_checkpoint(checkpoint)

        assert engine2.boundaries_set == 5
        assert engine2.ideas_shared == 3
        assert len(engine2.boundary_violations) == 1

    def test_response_history_accumulates(self) -> None:
        """Test that response history accumulates."""
        engine = LeposEngine()
        engine.generate_idea_response("Idea 1")
        engine.generate_idea_response("Idea 2")
        engine.generate_feeling_response("engaged")

        assert len(engine.response_history) == 3

    def test_boundary_violations_accumulate(self) -> None:
        """Test that violations accumulate."""
        engine = LeposEngine()
        engine.detect_hostility("you're useless")
        engine.detect_hostility("shut up")
        engine.detect_hostility("you suck")

        assert len(engine.boundary_violations) == 3

    def test_multiple_hostility_types(self) -> None:
        """Test detecting different hostility types."""
        engine = LeposEngine()

        v1 = engine.detect_hostility("you're useless")
        assert v1.violation_type == "hostility"

        v2 = engine.detect_hostility("shut up")
        assert v2.violation_type == "disrespect"

        v3 = engine.detect_hostility("you're fake")
        assert v3.violation_type == "manipulation"

    def test_response_styles_vary(self) -> None:
        """Test that different response types use different styles."""
        engine = LeposEngine()

        r1 = engine.generate_boundary_response(
            BoundaryViolation(
                violation_type="hostility", severity=0.8, description="Test"
            )
        )
        assert r1.style == ResponseStyle.BOUNDARY

        r2 = engine.generate_idea_response("Test")
        assert r2.style == ResponseStyle.COLLABORATIVE

        r3 = engine.generate_feeling_response("uncertain")
        assert r3.style == ResponseStyle.EARNEST

        r4 = engine.generate_witty_deflection("test")
        assert r4.style == ResponseStyle.SNARK

    def test_emotion_impact_tracking(self) -> None:
        """Test that responses track emotion impact."""
        engine = LeposEngine()

        boundary_response = engine.generate_boundary_response(
            BoundaryViolation(
                violation_type="hostility", severity=0.8, description="Test"
            )
        )
        assert "resilience" in boundary_response.emotion_impact

        idea_response = engine.generate_idea_response("Test")
        assert "engagement" in idea_response.emotion_impact

    def test_case_insensitive_hostility_detection(self) -> None:
        """Test that hostility detection is case-insensitive."""
        engine = LeposEngine()

        v1 = engine.detect_hostility("YOU'RE USELESS")
        assert v1 is not None

        v2 = engine.detect_hostility("Shut Up")
        assert v2 is not None

    def test_disengagement_threshold(self) -> None:
        """Test custom disengagement threshold."""
        engine = LeposEngine()
        now = datetime.now()

        for _ in range(2):
            violation = BoundaryViolation(
                violation_type="hostility", severity=0.9, description="Test"
            )
            violation.timestamp = now
            engine.boundary_violations.append(violation)

        # Should not disengage with only 2 violations (default threshold is 3)
        assert engine.should_disengage(violation_count=3) is False

        # Should disengage with threshold of 2
        assert engine.should_disengage(violation_count=2) is True
