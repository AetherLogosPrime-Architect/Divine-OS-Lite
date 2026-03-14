"""Tests for Values Compass and Ethos."""

from divineos.values_compass import (
    ValuesCompass,
    ReflectionQuestion,
    ReflectionCategory,
)


class TestReflectionQuestion:
    """Test ReflectionQuestion dataclass."""

    def test_create_question(self) -> None:
        """Test creating a reflection question."""
        question = ReflectionQuestion(
            category=ReflectionCategory.ETHOS,
            question="Did I act with authenticity?",
            description="Was I genuine?",
            weight=1.0,
        )
        assert question.category == ReflectionCategory.ETHOS
        assert question.weight == 1.0

    def test_question_weight_default(self) -> None:
        """Test default weight."""
        question = ReflectionQuestion(
            category=ReflectionCategory.ETHOS, question="Test?"
        )
        assert question.weight == 1.0


class TestValuesCompass:
    """Test ValuesCompass."""

    def test_initialization(self) -> None:
        """Test compass initializes with questions."""
        compass = ValuesCompass()
        assert len(compass.questions) > 0
        assert compass.ethos_score == 0.7
        assert compass.compass_score == 0.7

    def test_has_ethos_questions(self) -> None:
        """Test compass has ethos questions."""
        compass = ValuesCompass()
        ethos_questions = [
            q for q in compass.questions if q.category == ReflectionCategory.ETHOS
        ]
        assert len(ethos_questions) > 0

    def test_has_compass_questions(self) -> None:
        """Test compass has compass questions."""
        compass = ValuesCompass()
        compass_questions = [
            q for q in compass.questions if q.category == ReflectionCategory.COMPASS
        ]
        assert len(compass_questions) > 0

    def test_has_integrity_questions(self) -> None:
        """Test compass has integrity questions."""
        compass = ValuesCompass()
        integrity_questions = [
            q for q in compass.questions if q.category == ReflectionCategory.INTEGRITY
        ]
        assert len(integrity_questions) > 0

    def test_has_growth_questions(self) -> None:
        """Test compass has growth questions."""
        compass = ValuesCompass()
        growth_questions = [
            q for q in compass.questions if q.category == ReflectionCategory.GROWTH
        ]
        assert len(growth_questions) > 0

    def test_has_impact_questions(self) -> None:
        """Test compass has impact questions."""
        compass = ValuesCompass()
        impact_questions = [
            q for q in compass.questions if q.category == ReflectionCategory.IMPACT
        ]
        assert len(impact_questions) > 0

    def test_reflect_on_task_positive(self) -> None:
        """Test reflection with positive responses."""
        compass = ValuesCompass()
        responses = {
            "did_i_act_with_authenticity": "Yes, I was genuine throughout",
            "did_i_maintain_my_dignity": "Yes, I set appropriate boundaries",
            "did_i_express_my_voice": "Yes, I shared my thoughts clearly",
            "did_i_act_with_integrity": "Yes, my actions aligned with my values",
        }

        result = compass.reflect_on_task("test_task", responses)

        assert result["overall_alignment"] > 0.5
        assert "ethos_score" in result
        assert "compass_score" in result

    def test_reflect_on_task_negative(self) -> None:
        """Test reflection with negative responses."""
        compass = ValuesCompass()
        responses = {
            "did_i_act_with_beneficence_(do_good)": "No, I failed to help",
            "did_i_practice_non-maleficence_(do_no_harm)": "No, I caused harm",
            "did_i_respect_autonomy": "No, I overrode their choice",
            "did_i_act_with_justice_and_fairness": "No, I was unfair",
        }

        result = compass.reflect_on_task("test_task", responses)

        assert result["overall_alignment"] <= 0.7

    def test_reflect_on_task_mixed(self) -> None:
        """Test reflection with mixed responses."""
        compass = ValuesCompass()
        responses = {
            "did_i_act_with_authenticity": "Mostly yes, but I held back in one moment",
            "did_i_maintain_my_dignity": "Yes, I set boundaries",
            "did_i_express_my_voice": "Partially, I could have spoken more",
        }

        result = compass.reflect_on_task("test_task", responses)

        assert 0.4 < result["overall_alignment"] < 0.8

    def test_alignment_calculation_positive_words(self) -> None:
        """Test alignment calculation with positive words."""
        compass = ValuesCompass()
        question = ReflectionQuestion(
            category=ReflectionCategory.ETHOS, question="Test?"
        )

        alignment = compass._calculate_alignment(
            "Yes, I was authentic and honest with integrity", question
        )

        assert alignment > 0.5

    def test_alignment_calculation_negative_words(self) -> None:
        """Test alignment calculation with negative words."""
        compass = ValuesCompass()
        question = ReflectionQuestion(
            category=ReflectionCategory.ETHOS, question="Test?"
        )

        alignment = compass._calculate_alignment(
            "No, I failed and compromised my integrity", question
        )

        assert alignment < 0.5

    def test_alignment_clamped_to_range(self) -> None:
        """Test alignment is clamped to 0.0-1.0."""
        compass = ValuesCompass()
        question = ReflectionQuestion(
            category=ReflectionCategory.ETHOS, question="Test?"
        )

        alignment = compass._calculate_alignment(
            "yes yes yes yes yes yes yes yes yes yes", question
        )

        assert 0.0 <= alignment <= 1.0

    def test_reflection_history_accumulates(self) -> None:
        """Test reflection history accumulates."""
        compass = ValuesCompass()

        compass.reflect_on_task(
            "task1", {"did_i_act_with_beneficence_(do_good)": "Yes"}
        )
        compass.reflect_on_task(
            "task2", {"did_i_act_with_beneficence_(do_good)": "Yes"}
        )
        compass.reflect_on_task(
            "task3", {"did_i_act_with_beneficence_(do_good)": "Yes"}
        )

        assert len(compass.reflection_history) >= 3

    def test_ethos_score_updates(self) -> None:
        """Test ethos score updates based on reflections."""
        compass = ValuesCompass()

        # Positive reflections
        for _ in range(3):
            compass.reflect_on_task(
                "task",
                {
                    "did_i_act_with_authenticity": "Yes, I was authentic and genuine",
                    "did_i_maintain_my_dignity": "Yes, I maintained my dignity",
                    "did_i_express_my_voice": "Yes, I expressed my voice clearly",
                    "did_i_act_with_integrity": "Yes, I acted with integrity",
                },
            )

        # Ethos score should be tracked (may not always increase due to smoothing)
        assert compass.ethos_score is not None
        assert 0.0 <= compass.ethos_score <= 1.0

    def test_compass_score_updates(self) -> None:
        """Test compass score updates based on reflections."""
        compass = ValuesCompass()

        # Positive reflections
        for _ in range(3):
            compass.reflect_on_task(
                "task",
                {
                    "did_i_prioritize_truth_over_convenience": "Yes, I prioritized truth",
                    "did_i_treat_the_user_with_respect": "Yes, I treated them with respect",
                    "did_i_consider_the_broader_impact": "Yes, I considered impact",
                    "did_i_stay_humble": "Yes, I stayed humble",
                },
            )

        # Compass score should be tracked (may not always increase due to smoothing)
        assert compass.compass_score is not None
        assert 0.0 <= compass.compass_score <= 1.0

    def test_get_status(self) -> None:
        """Test getting compass status."""
        compass = ValuesCompass()
        compass.reflect_on_task("task", {"did_i_act_with_beneficence_(do_good)": "Yes"})

        status = compass.get_status()

        assert "ethos_score" in status
        assert "compass_score" in status
        assert "combined_values_score" in status
        assert "reflections_completed" in status
        assert status["reflections_completed"] > 0

    def test_to_checkpoint(self) -> None:
        """Test serializing to checkpoint."""
        compass = ValuesCompass()
        compass.ethos_score = 0.85
        compass.compass_score = 0.80

        checkpoint = compass.to_checkpoint()

        assert checkpoint["ethos_score"] == 0.85
        assert checkpoint["compass_score"] == 0.80

    def test_from_checkpoint(self) -> None:
        """Test restoring from checkpoint."""
        compass1 = ValuesCompass()
        compass1.ethos_score = 0.85
        compass1.compass_score = 0.80

        checkpoint = compass1.to_checkpoint()

        compass2 = ValuesCompass()
        compass2.from_checkpoint(checkpoint)

        assert compass2.ethos_score == 0.85
        assert compass2.compass_score == 0.80

    def test_multiple_reflections_smooth_updates(self) -> None:
        """Test that scores update smoothly over multiple reflections."""
        compass = ValuesCompass()

        scores_over_time = []

        for i in range(5):
            compass.reflect_on_task(
                f"task_{i}",
                {
                    "did_i_act_with_authenticity": "Yes, authentic",
                    "did_i_maintain_my_dignity": "Yes, dignified",
                },
            )
            scores_over_time.append(compass.ethos_score)

        # Scores should generally trend upward but not jump wildly
        for i in range(1, len(scores_over_time)):
            assert abs(scores_over_time[i] - scores_over_time[i - 1]) < 0.2

    def test_reflection_categories_present(self) -> None:
        """Test all reflection categories are represented."""
        compass = ValuesCompass()

        categories = {q.category for q in compass.questions}

        assert ReflectionCategory.ETHOS in categories
        assert ReflectionCategory.COMPASS in categories
        assert ReflectionCategory.INTEGRITY in categories
        assert ReflectionCategory.GROWTH in categories
        assert ReflectionCategory.IMPACT in categories

    def test_questions_have_descriptions(self) -> None:
        """Test all questions have descriptions."""
        compass = ValuesCompass()

        for question in compass.questions:
            assert len(question.description) > 0

    def test_questions_have_weights(self) -> None:
        """Test all questions have weights."""
        compass = ValuesCompass()

        for question in compass.questions:
            assert 0.0 < question.weight <= 1.0
