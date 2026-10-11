"""
Comprehensive Unit Tests for GPA Calculation Engine.
Tests all deterministic functions, edge cases, input validation, and formulas.
"""

import pytest
import math
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.calculator import (
    calculate_sgpa,
    calculate_cgpa,
    predict_target_gpa,
    analyze_what_if,
    analyze_backlog_impact,
    validate_credit,
    validate_grade_point,
    resolve_grade_point,
    CalculationError,
    DEFAULT_SPPU_SCALE
)


class TestValidationAndResolution:
    def test_validate_credit_valid(self):
        assert validate_credit(4.0) == 4.0
        assert validate_credit(1) == 1.0
        assert validate_credit(0.5) == 0.5

    def test_validate_credit_invalid(self):
        with pytest.raises(CalculationError, match="strictly positive"):
            validate_credit(0.0)
        with pytest.raises(CalculationError, match="strictly positive"):
            validate_credit(-2.0)
        with pytest.raises(CalculationError, match="NaN or infinite"):
            validate_credit(float("nan"))
        with pytest.raises(CalculationError, match="must be a number"):
            validate_credit("four")  # type: ignore

    def test_validate_grade_point_valid(self):
        assert validate_grade_point(10.0) == 10.0
        assert validate_grade_point(0.0) == 0.0
        assert validate_grade_point(8.5) == 8.5

    def test_validate_grade_point_invalid(self):
        with pytest.raises(CalculationError, match="cannot be negative"):
            validate_grade_point(-1.0)
        with pytest.raises(CalculationError, match="exceeds maximum scale"):
            validate_grade_point(10.5, max_scale=10.0)
        with pytest.raises(CalculationError, match="NaN or infinite"):
            validate_grade_point(float("inf"))

    def test_resolve_grade_point_letters(self):
        assert resolve_grade_point(grade="O") == 10.0
        assert resolve_grade_point(grade="A+") == 9.0
        assert resolve_grade_point(grade="a") == 8.0
        assert resolve_grade_point(grade="B+") == 7.0
        assert resolve_grade_point(grade="b") == 6.0
        assert resolve_grade_point(grade="C") == 5.0
        assert resolve_grade_point(grade="P") == 4.0
        assert resolve_grade_point(grade="F") == 0.0
        assert resolve_grade_point(grade="Ab") == 0.0

    def test_resolve_grade_point_unknown_grade(self):
        with pytest.raises(CalculationError, match="Unrecognized letter grade"):
            resolve_grade_point(grade="Z")


class TestSGPACalculator:
    def test_sgpa_standard_case(self):
        # 4 cr * 10 (O) = 40
        # 4 cr * 9 (A+) = 36
        # 3 cr * 8 (A) = 24
        # 3 cr * 7 (B+) = 21
        # Total Credits = 14
        # Total Weighted Points = 121
        # SGPA = 121 / 14 = 8.6428... -> 8.64
        subjects = [
            {"name": "Maths", "credit": 4.0, "grade": "O"},
            {"name": "Physics", "credit": 4.0, "grade": "A+"},
            {"name": "Electrical", "credit": 3.0, "grade": "A"},
            {"name": "Graphics", "credit": 3.0, "grade": "B+"}
        ]
        res = calculate_sgpa(subjects)
        assert res["sgpa"] == 8.64
        assert res["total_credits"] == 14.0
        assert res["total_weighted_points"] == 121.0
        assert res["has_backlog"] is False
        assert res["subject_count"] == 4

    def test_sgpa_with_direct_grade_points(self):
        subjects = [
            {"name": "Sub 1", "credit": 4.0, "grade_point": 9.0},
            {"name": "Sub 2", "credit": 4.0, "grade_point": 7.0}
        ]
        # Total points = 36 + 28 = 64 / 8 = 8.0
        res = calculate_sgpa(subjects)
        assert res["sgpa"] == 8.0
        assert res["total_credits"] == 8.0

    def test_sgpa_with_backlog_detection(self):
        subjects = [
            {"name": "Core Subject", "credit": 4.0, "grade": "F"},
            {"name": "Elective", "credit": 3.0, "grade": "A"}
        ]
        res = calculate_sgpa(subjects)
        assert res["has_backlog"] is True
        assert res["subjects"][0]["is_backlog"] is True
        assert res["subjects"][1]["is_backlog"] is False

    def test_sgpa_empty_subjects(self):
        with pytest.raises(CalculationError, match="At least one subject"):
            calculate_sgpa([])

    def test_sgpa_missing_credits(self):
        with pytest.raises(CalculationError, match="missing credit"):
            calculate_sgpa([{"name": "Course 1", "grade": "A"}])


class TestCGPACalculator:
    def test_cgpa_weighted_vs_unweighted_distinction(self):
        # Semester 1: 20 credits, SGPA 8.0 -> 160 pts
        # Semester 2: 30 credits, SGPA 9.0 -> 270 pts
        # Total Credits: 50
        # Total Weighted Points: 430
        # Weighted CGPA: 430 / 50 = 8.60
        # Simple Average: (8.0 + 9.0) / 2 = 8.50
        semesters = [
            {"name": "Sem 1", "sgpa": 8.0, "credits": 20.0},
            {"name": "Sem 2", "sgpa": 9.0, "credits": 30.0}
        ]
        res = calculate_cgpa(semesters)
        assert res["cgpa"] == 8.60
        assert res["simple_average"] == 8.50
        assert res["difference_from_simple_average"] == 0.10
        assert res["total_credits"] == 50.0

    def test_cgpa_uniform_credits(self):
        semesters = [
            {"name": "Sem 1", "sgpa": 8.0, "credits": 20.0},
            {"name": "Sem 2", "sgpa": 8.5, "credits": 20.0}
        ]
        res = calculate_cgpa(semesters)
        assert res["cgpa"] == 8.25
        assert res["simple_average"] == 8.25
        assert res["difference_from_simple_average"] == 0.0

    def test_cgpa_empty_semesters(self):
        with pytest.raises(CalculationError, match="At least one semester"):
            calculate_cgpa([])


class TestTargetGPAPredictor:
    def test_target_gpa_achievable(self):
        # Current CGPA: 7.5, completed: 60 credits -> 450 pts
        # Target CGPA: 8.0, total: 80 credits -> 640 pts needed
        # Remaining credits: 20 -> needed points = 640 - 450 = 190
        # Required SGPA = 190 / 20 = 9.5
        res = predict_target_gpa(
            current_cgpa=7.5,
            completed_credits=60.0,
            remaining_credits=20.0,
            target_cgpa=8.0,
            max_scale=10.0
        )
        assert res["achievable"] is True
        assert res["required_sgpa"] == 9.5
        assert res["max_achievable_cgpa"] == 8.12  # (450 + 200)/80 = 8.125 -> 8.12 or 8.13

    def test_target_gpa_impossible(self):
        # Current CGPA: 6.0, completed: 80 credits -> 480 pts
        # Target CGPA: 9.0, total: 100 credits -> 900 pts needed
        # Remaining credits: 20 -> needed points = 900 - 480 = 420
        # Required SGPA = 420 / 20 = 21.0 (impossible on 10.0 scale)
        # Max achievable with 10.0 in remaining: (480 + 200) / 100 = 6.80
        res = predict_target_gpa(
            current_cgpa=6.0,
            completed_credits=80.0,
            remaining_credits=20.0,
            target_cgpa=9.0,
            max_scale=10.0
        )
        assert res["achievable"] is False
        assert res["status"] == "impossible"
        assert res["required_sgpa"] == 21.0
        assert res["max_achievable_cgpa"] == 6.80

    def test_target_gpa_already_achieved(self):
        # Current points: 9.0 * 60 = 540. Target total needed: 6.0 * 80 = 480.
        # Needed: -60 points. Required SGPA <= 0.
        res = predict_target_gpa(
            current_cgpa=9.0,
            completed_credits=60.0,
            remaining_credits=20.0,
            target_cgpa=6.0,
            max_scale=10.0
        )
        assert res["achievable"] is True
        assert res["status"] == "already_achieved"
        assert res["required_sgpa"] <= 0.0

    def test_target_gpa_comfortably_achieved(self):
        # Current: 9.0 * 60 = 540. Target: 7.0 * 80 = 560. Needed: 20 points -> SGPA 1.0 <= 4.0
        res = predict_target_gpa(
            current_cgpa=9.0,
            completed_credits=60.0,
            remaining_credits=20.0,
            target_cgpa=7.0,
            max_scale=10.0
        )
        assert res["achievable"] is True
        assert res["status"] == "comfortably_achieved"
        assert res["required_sgpa"] == 1.0


class TestWhatIfAnalysis:
    def test_what_if_sgpa_grade_upgrade(self):
        baseline_subjects = [
            {"name": "Sub 1", "credit": 4.0, "grade": "B"},  # 6 * 4 = 24
            {"name": "Sub 2", "credit": 4.0, "grade": "A"}   # 8 * 4 = 32 -> SGPA = 56/8 = 7.0
        ]
        # Modify Sub 1 from B (6) to O (10):
        # New points = 40 + 32 = 72 / 8 = 9.0 (+2.0 delta)
        mods = [{"name": "Sub 1", "grade": "O"}]
        res = analyze_what_if(
            baseline_type="sgpa",
            baseline_data={"subjects": baseline_subjects},
            modifications=mods
        )
        assert res["baseline_score"] == 7.0
        assert res["simulated_score"] == 9.0
        assert res["delta"] == 2.0
        assert res["delta_direction"] == "positive"

    def test_what_if_cgpa_add_future_semester(self):
        semesters = [
            {"name": "Sem 1", "sgpa": 8.0, "credits": 20.0}
        ]
        mods = [{"add_semester": True, "name": "Sem 2", "sgpa": 9.0, "credits": 20.0}]
        res = analyze_what_if(
            baseline_type="cgpa",
            baseline_data={"semesters": semesters},
            modifications=mods
        )
        assert res["baseline_score"] == 8.0
        assert res["simulated_score"] == 8.5
        assert res["delta"] == 0.5


class TestBacklogImpactAnalysis:
    def test_backlog_clearance_replacement(self):
        # Semester 1 had F grade (0 GP) for a 4 credit subject
        # Say student currently has CGPA 7.0 across 40 credits (280 points)
        semesters = [
            {"name": "Sem 1", "sgpa": 7.0, "credits": 40.0}
        ]
        backlogs = [
            {"name": "Maths Backlog", "credit": 4.0, "target_grade": "A"}  # A = 8.0 -> 32 pts gain
        ]
        # Points gain = 32
        # New total points = 280 + 32 = 312
        # New CGPA = 312 / 40 = 7.80
        res = analyze_backlog_impact(
            semesters=semesters,
            backlog_subjects=backlogs,
            rule_type="replacement"
        )
        assert res["baseline_cgpa"] == 7.0
        assert res["simulated_cgpa_after_clearing"] == 7.80
        assert res["cgpa_boost"] == 0.80
        assert res["total_backlog_credits"] == 4.0
