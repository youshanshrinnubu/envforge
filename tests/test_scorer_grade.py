"""Additional grade/boundary tests for envforge.scorer."""

import pytest
from envforge.scorer import ScoreResult, MAX_SCORE


@pytest.mark.parametrize("score,expected_grade", [
    (100, "A"),
    (90, "A"),
    (89, "B"),
    (75, "B"),
    (74, "C"),
    (60, "C"),
    (59, "D"),
    (40, "D"),
    (39, "F"),
    (0, "F"),
])
def test_grade_boundaries(score, expected_grade):
    result = ScoreResult(score=score, max_score=MAX_SCORE)
    assert result.grade == expected_grade


@pytest.mark.parametrize("score,expected_pct", [
    (100, 100.0),
    (50, 50.0),
    (0, 0.0),
    (75, 75.0),
])
def test_percentage_values(score, expected_pct):
    result = ScoreResult(score=score, max_score=MAX_SCORE)
    assert result.percentage == expected_pct


def test_score_result_default_breakdown_empty():
    result = ScoreResult(score=50)
    assert result.breakdown == {}


def test_score_result_default_suggestions_empty():
    result = ScoreResult(score=50)
    assert result.suggestions == []


def test_score_result_max_score_default():
    result = ScoreResult(score=70)
    assert result.max_score == MAX_SCORE
