"""
GPA Calculation Engine
Deterministic numerical calculation functions for SGPA, CGPA, Target GPA prediction,
What-If analysis, and Backlog impact analysis.
"""

from typing import List, Dict, Optional, Any, Tuple
import math

# Default SPPU 10-point Choice Based Credit System (CBCS) grading scale
DEFAULT_SPPU_SCALE: Dict[str, float] = {
    "O": 10.0,   # Outstanding (90-100%)
    "A+": 9.0,   # Excellent (80-89%)
    "A": 8.0,    # Very Good (70-79%)
    "B+": 7.0,   # Good (60-69%)
    "B": 6.0,    # Above Average (55-59%)
    "C": 5.0,    # Average (50-54%)
    "P": 4.0,    # Pass (40-49%)
    "F": 0.0,    # Fail (<40%)
    "Ab": 0.0    # Absent
}

DEFAULT_MAX_SCALE: float = 10.0
PASSING_GRADE_POINT: float = 4.0


class CalculationError(Exception):
    """Custom exception for GPA calculation validation and mathematical errors."""
    pass


def validate_grade_point(grade_point: float, max_scale: float = DEFAULT_MAX_SCALE) -> float:
    """Validates that a numerical grade point is within valid bounds."""
    if not isinstance(grade_point, (int, float)):
        raise CalculationError(f"Grade point must be a number, received: {type(grade_point).__name__}")
    if math.isnan(grade_point) or math.isinf(grade_point):
        raise CalculationError("Grade point cannot be NaN or infinite")
    if grade_point < 0.0:
        raise CalculationError(f"Grade point cannot be negative ({grade_point})")
    if grade_point > max_scale:
        raise CalculationError(f"Grade point ({grade_point}) exceeds maximum scale ({max_scale})")
    return float(grade_point)


def validate_credit(credit: float) -> float:
    """Validates that subject credit is strictly positive."""
    if not isinstance(credit, (int, float)):
        raise CalculationError(f"Credit must be a number, received: {type(credit).__name__}")
    if math.isnan(credit) or math.isinf(credit):
        raise CalculationError("Credit cannot be NaN or infinite")
    if credit <= 0.0:
        raise CalculationError(f"Credit must be strictly positive (> 0), received: {credit}")
    return float(credit)


def resolve_grade_point(
    grade: Optional[str] = None,
    grade_point: Optional[float] = None,
    scheme: Optional[Dict[str, float]] = None,
    max_scale: float = DEFAULT_MAX_SCALE
) -> float:
    """
    Resolves letter grade or direct grade point to a validated numeric grade point.
    """
    active_scheme = scheme or DEFAULT_SPPU_SCALE

    if grade_point is not None:
        return validate_grade_point(grade_point, max_scale)
    
    if grade is not None:
        normalized_grade = grade.strip().upper()
        # Handle variations like "A+" or "a+"
        for k, v in active_scheme.items():
            if k.upper() == normalized_grade:
                return validate_grade_point(v, max_scale)
        raise CalculationError(
            f"Unrecognized letter grade '{grade}'. Allowed in selected scheme: {list(active_scheme.keys())}"
        )

    raise CalculationError("Either 'grade' (letter) or 'grade_point' (numeric) must be provided.")


def calculate_sgpa(
    subjects: List[Dict[str, Any]],
    scheme: Optional[Dict[str, float]] = None,
    max_scale: float = DEFAULT_MAX_SCALE
) -> Dict[str, Any]:
    """
    Calculates Semester Grade Point Average (SGPA).
    Formula: SGPA = Sum(Credit_i * GradePoint_i) / Sum(Credit_i)
    """
    if not subjects or len(subjects) == 0:
        raise CalculationError("At least one subject must be provided to calculate SGPA.")

    total_credits = 0.0
    total_weighted_points = 0.0
    detailed_subjects = []
    has_backlog = False

    for idx, subj in enumerate(subjects, start=1):
        name = str(subj.get("name", f"Subject {idx}")).strip() or f"Subject {idx}"
        code = str(subj.get("code", "")).strip()
        raw_credit = subj.get("credit", subj.get("credits"))

        if raw_credit is None:
            raise CalculationError(f"Subject '{name}' is missing credit value.")

        credit = validate_credit(raw_credit)
        grade_letter = subj.get("grade")
        gp_input = subj.get("grade_point")

        gp = resolve_grade_point(grade=grade_letter, grade_point=gp_input, scheme=scheme, max_scale=max_scale)
        weighted_points = credit * gp

        is_failed = gp < PASSING_GRADE_POINT
        if is_failed:
            has_backlog = True

        detailed_subjects.append({
            "name": name,
            "code": code,
            "credit": credit,
            "grade_letter": grade_letter.upper() if grade_letter else None,
            "grade_point": gp,
            "weighted_points": round(weighted_points, 4),
            "is_backlog": is_failed
        })

        total_credits += credit
        total_weighted_points += weighted_points

    if total_credits <= 0.0:
        raise CalculationError("Sum of credits must be strictly greater than 0.")

    raw_sgpa = total_weighted_points / total_credits
    rounded_sgpa = round(raw_sgpa, 2)

    return {
        "sgpa": rounded_sgpa,
        "sgpa_exact": raw_sgpa,
        "total_credits": round(total_credits, 2),
        "total_weighted_points": round(total_weighted_points, 4),
        "subject_count": len(detailed_subjects),
        "subjects": detailed_subjects,
        "has_backlog": has_backlog,
        "formula": "SGPA = Σ(Credit × Grade Point) / Σ(Credits)"
    }


def calculate_cgpa(
    semesters: List[Dict[str, Any]],
    max_scale: float = DEFAULT_MAX_SCALE
) -> Dict[str, Any]:
    """
    Calculates Cumulative Grade Point Average (CGPA).
    Formula: CGPA = Sum(Semester_SGPA_j * Semester_Credits_j) / Sum(Semester_Credits_j)
    
    Also computes the unweighted simple average of SGPAs to clearly illustrate the difference.
    """
    if not semesters or len(semesters) == 0:
        raise CalculationError("At least one semester record is required to calculate CGPA.")

    total_applicable_credits = 0.0
    total_weighted_sgpa_points = 0.0
    sgpa_sum = 0.0
    detailed_semesters = []

    for idx, sem in enumerate(semesters, start=1):
        sem_name = str(sem.get("name", f"Semester {idx}")).strip() or f"Semester {idx}"
        raw_sgpa = sem.get("sgpa")
        raw_credits = sem.get("credit", sem.get("credits"))

        if raw_sgpa is None:
            raise CalculationError(f"Semester '{sem_name}' is missing SGPA.")
        if raw_credits is None:
            raise CalculationError(f"Semester '{sem_name}' is missing earned/applicable credits.")

        sgpa = validate_grade_point(float(raw_sgpa), max_scale=max_scale)
        credits = validate_credit(float(raw_credits))

        weighted_sem_points = sgpa * credits
        total_applicable_credits += credits
        total_weighted_sgpa_points += weighted_sem_points
        sgpa_sum += sgpa

        detailed_semesters.append({
            "name": sem_name,
            "sgpa": round(sgpa, 2),
            "credits": round(credits, 2),
            "weighted_points": round(weighted_sem_points, 4)
        })

    if total_applicable_credits <= 0.0:
        raise CalculationError("Total applicable credits must be strictly positive.")

    raw_cgpa = total_weighted_sgpa_points / total_applicable_credits
    rounded_cgpa = round(raw_cgpa, 2)
    simple_average = round(sgpa_sum / len(semesters), 2)
    is_equal_to_average = abs(rounded_cgpa - simple_average) < 0.0001

    explanation = (
        "Weighted CGPA accounts for varying credit weights per semester. "
        + ("In your case, semester credits vary, so weighted CGPA correctly reflects subject workload."
           if not is_equal_to_average else "In your case, semester credits are uniform, so weighted CGPA equals simple average.")
    )

    return {
        "cgpa": rounded_cgpa,
        "cgpa_exact": raw_cgpa,
        "simple_average": simple_average,
        "difference_from_simple_average": round(rounded_cgpa - simple_average, 2),
        "total_credits": round(total_applicable_credits, 2),
        "total_weighted_points": round(total_weighted_sgpa_points, 4),
        "semester_count": len(detailed_semesters),
        "semesters": detailed_semesters,
        "formula": "CGPA = Σ(Semester SGPA × Semester Credits) / Σ(Semester Credits)",
        "explanation": explanation
    }


def predict_target_gpa(
    current_cgpa: float,
    completed_credits: float,
    remaining_credits: float,
    target_cgpa: float,
    max_scale: float = DEFAULT_MAX_SCALE
) -> Dict[str, Any]:
    """
    Calculates the required average SGPA in remaining credits to achieve a target CGPA.
    
    Formula:
    Target CGPA = (Current CGPA * Completed Credits + Required SGPA * Remaining Credits) / Total Credits
    Required SGPA = [Target CGPA * (Completed Credits + Remaining Credits) - (Current CGPA * Completed Credits)] / Remaining Credits
    """
    current_cgpa = validate_grade_point(current_cgpa, max_scale)
    target_cgpa = validate_grade_point(target_cgpa, max_scale)

    if completed_credits < 0.0:
        raise CalculationError("Completed credits cannot be negative.")
    if remaining_credits <= 0.0:
        raise CalculationError("Remaining credits must be strictly positive (> 0) to predict required GPA.")

    total_credits = completed_credits + remaining_credits
    
    # Required total weighted points for target
    target_total_points = target_cgpa * total_credits
    current_total_points = current_cgpa * completed_credits
    needed_points = target_total_points - current_total_points

    required_sgpa_raw = needed_points / remaining_credits
    required_sgpa = round(required_sgpa_raw, 2)

    # Maximum possible CGPA if student scores max_scale (10.0) in all remaining credits
    max_possible_points = current_total_points + (max_scale * remaining_credits)
    max_achievable_cgpa = round(max_possible_points / total_credits, 2)

    # Status classification
    if required_sgpa <= 0.0:
        achievable = True
        status = "already_achieved"
        message = (
            f"Your current CGPA ({current_cgpa:.2f}) across {completed_credits} credits already secures your target "
            f"({target_cgpa:.2f}) mathematically even with 0 additional grade points."
        )
    elif required_sgpa <= PASSING_GRADE_POINT:
        achievable = True
        status = "comfortably_achieved"
        message = (
            f"To achieve a target CGPA of {target_cgpa:.2f}, you need an average SGPA of {required_sgpa:.2f} "
            f"across your remaining {remaining_credits} credits. This is comfortably achievable with basic passing grades."
        )
    elif required_sgpa <= max_scale:
        achievable = True
        if required_sgpa <= 7.0:
            status = "achievable_moderate"
        elif required_sgpa <= 8.5:
            status = "achievable_good_effort"
        else:
            status = "achievable_high_effort"
        message = (
            f"To achieve a target CGPA of {target_cgpa:.2f}, you need an average SGPA of {required_sgpa:.2f} "
            f"across your remaining {remaining_credits} credits. This is mathematically achievable on the {max_scale}-point scale."
        )
    else:
        achievable = False
        status = "impossible"
        message = (
            f"A target CGPA of {target_cgpa:.2f} is mathematically impossible because it requires an SGPA of "
            f"{required_sgpa:.2f}, exceeding the maximum scale of {max_scale:.1f}. "
            f"The absolute highest CGPA you can achieve with a perfect {max_scale:.1f} in all remaining credits is {max_achievable_cgpa:.2f}."
        )

    # Generate scenario projections for remaining credits at benchmark SGPAs
    scenarios = []
    benchmark_sgpas = [6.0, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
    for bench in benchmark_sgpas:
        if bench <= max_scale:
            proj_total_points = current_total_points + (bench * remaining_credits)
            proj_cgpa = round(proj_total_points / total_credits, 2)
            scenarios.append({
                "hypothetical_remaining_sgpa": bench,
                "resulting_cgpa": proj_cgpa,
                "meets_target": proj_cgpa >= target_cgpa,
                "delta_from_target": round(proj_cgpa - target_cgpa, 2)
            })

    return {
        "achievable": achievable,
        "status": status,
        "required_sgpa": required_sgpa,
        "required_sgpa_exact": required_sgpa_raw,
        "target_cgpa": target_cgpa,
        "current_cgpa": current_cgpa,
        "completed_credits": completed_credits,
        "remaining_credits": remaining_credits,
        "total_credits": total_credits,
        "max_scale": max_scale,
        "max_achievable_cgpa": max_achievable_cgpa,
        "message": message,
        "scenarios": scenarios
    }


def analyze_what_if(
    baseline_type: str,  # "sgpa" or "cgpa"
    baseline_data: Dict[str, Any],
    modifications: List[Dict[str, Any]],
    scheme: Optional[Dict[str, float]] = None,
    max_scale: float = DEFAULT_MAX_SCALE
) -> Dict[str, Any]:
    """
    Performs 'What-If' hypothetical simulation.
    baseline_type: 'sgpa' (modifying subject grades) or 'cgpa' (modifying semester SGPAs or adding future semesters)
    """
    if baseline_type == "sgpa":
        # Baseline SGPA
        orig_subjects = baseline_data.get("subjects", [])
        if not orig_subjects:
            raise CalculationError("Baseline subjects are required for SGPA What-If analysis.")

        baseline_res = calculate_sgpa(orig_subjects, scheme=scheme, max_scale=max_scale)

        # Clone and apply modifications: list of {index or name, new_grade or new_grade_point}
        hypothetical_subjects = [dict(s) for s in orig_subjects]
        for mod in modifications:
            target_idx = mod.get("index")
            target_name = str(mod.get("name", "")).strip().lower()
            new_grade = mod.get("grade")
            new_gp = mod.get("grade_point")

            matched = False
            for i, subj in enumerate(hypothetical_subjects):
                if target_idx is not None and i == target_idx:
                    if new_grade is not None:
                        subj["grade"] = new_grade
                        subj.pop("grade_point", None)
                    elif new_gp is not None:
                        subj["grade_point"] = new_gp
                        subj.pop("grade", None)
                    matched = True
                    break
                elif target_name and subj.get("name", "").strip().lower() == target_name:
                    if new_grade is not None:
                        subj["grade"] = new_grade
                        subj.pop("grade_point", None)
                    elif new_gp is not None:
                        subj["grade_point"] = new_gp
                        subj.pop("grade", None)
                    matched = True
                    break

            if not matched and mod.get("add_subject"):
                # Adding a hypothetical subject
                hypothetical_subjects.append({
                    "name": mod.get("name", "Hypothetical Subject"),
                    "credit": mod.get("credit", 3.0),
                    "grade": mod.get("grade"),
                    "grade_point": mod.get("grade_point")
                })

        simulated_res = calculate_sgpa(hypothetical_subjects, scheme=scheme, max_scale=max_scale)
        delta = round(simulated_res["sgpa"] - baseline_res["sgpa"], 2)

        return {
            "type": "sgpa",
            "baseline_score": baseline_res["sgpa"],
            "simulated_score": simulated_res["sgpa"],
            "delta": delta,
            "delta_direction": "positive" if delta > 0 else ("negative" if delta < 0 else "neutral"),
            "baseline_details": baseline_res,
            "simulated_details": simulated_res,
            "label": "Hypothetical SGPA Simulation"
        }

    elif baseline_type == "cgpa":
        orig_semesters = baseline_data.get("semesters", [])
        if not orig_semesters:
            raise CalculationError("Baseline semesters are required for CGPA What-If analysis.")

        baseline_res = calculate_cgpa(orig_semesters, max_scale=max_scale)

        hypothetical_semesters = [dict(s) for s in orig_semesters]
        for mod in modifications:
            target_idx = mod.get("index")
            target_name = str(mod.get("name", "")).strip().lower()

            if mod.get("add_semester"):
                hypothetical_semesters.append({
                    "name": mod.get("name", f"Semester {len(hypothetical_semesters) + 1}"),
                    "sgpa": mod.get("sgpa", 8.0),
                    "credits": mod.get("credits", mod.get("credit", 20.0))
                })
            else:
                for i, sem in enumerate(hypothetical_semesters):
                    if (target_idx is not None and i == target_idx) or (target_name and sem.get("name", "").strip().lower() == target_name):
                        if "sgpa" in mod:
                            sem["sgpa"] = mod["sgpa"]
                        if "credits" in mod:
                            sem["credits"] = mod["credits"]
                        break

        simulated_res = calculate_cgpa(hypothetical_semesters, max_scale=max_scale)
        delta = round(simulated_res["cgpa"] - baseline_res["cgpa"], 2)

        return {
            "type": "cgpa",
            "baseline_score": baseline_res["cgpa"],
            "simulated_score": simulated_res["cgpa"],
            "delta": delta,
            "delta_direction": "positive" if delta > 0 else ("negative" if delta < 0 else "neutral"),
            "baseline_details": baseline_res,
            "simulated_details": simulated_res,
            "label": "Hypothetical CGPA Simulation"
        }
    else:
        raise CalculationError(f"Unsupported baseline_type '{baseline_type}'. Must be 'sgpa' or 'cgpa'.")


def analyze_backlog_impact(
    semesters: List[Dict[str, Any]],
    backlog_subjects: List[Dict[str, Any]],
    rule_type: str = "replacement",
    scheme: Optional[Dict[str, float]] = None,
    max_scale: float = DEFAULT_MAX_SCALE
) -> Dict[str, Any]:
    """
    Analyzes the impact of backlog clearance / grade improvement.
    rule_type options:
      - 'replacement': Replaces the failing grade (0 GP) with the cleared grade in the original semester.
      - 'current_attempt_only': Baseline keeps 0 credit earned; cleared subject is added to latest term.
      - 'penalty_cap': Max grade point on cleared subject capped at specified value (e.g. 7.0 / B+).
    """
    active_scheme = scheme or DEFAULT_SPPU_SCALE
    baseline_cgpa_res = calculate_cgpa(semesters, max_scale=max_scale)

    cleared_scenarios = []
    
    # Copy semesters for replacement simulation
    simulated_semesters = [dict(s) for s in semesters]

    total_backlog_credits = sum(validate_credit(b.get("credit", b.get("credits", 3.0))) for b in backlog_subjects)

    for item in backlog_subjects:
        sub_name = item.get("name", "Backlog Subject")
        sub_credit = validate_credit(item.get("credit", item.get("credits", 3.0)))
        semester_index = item.get("semester_index", 0)  # 0-indexed
        target_cleared_grade = item.get("target_grade", "A")

        target_gp = resolve_grade_point(grade=target_cleared_grade, scheme=active_scheme, max_scale=max_scale)

        if rule_type == "penalty_cap":
            cap = item.get("penalty_cap", 7.0)
            target_gp = min(target_gp, cap)

        cleared_scenarios.append({
            "subject_name": sub_name,
            "credits": sub_credit,
            "target_grade": target_cleared_grade,
            "cleared_grade_point": target_gp,
            "points_gain": round(target_gp * sub_credit, 2)
        })

    # In replacement rule, semester where subject occurred gains (cleared_gp * credit)
    # If original semester had F (0 GP), points gained is sum of (cleared_gp * credit)
    additional_points = sum(sc["points_gain"] for sc in cleared_scenarios)
    current_total_points = baseline_cgpa_res["total_weighted_points"]
    total_credits = baseline_cgpa_res["total_credits"]

    simulated_total_points = current_total_points + additional_points
    simulated_cgpa_raw = simulated_total_points / total_credits
    simulated_cgpa = round(simulated_cgpa_raw, 2)
    delta = round(simulated_cgpa - baseline_cgpa_res["cgpa"], 2)

    rule_descriptions = {
        "replacement": (
            "SPPU CBCS Grade Replacement Scenario: When a backlog course is cleared, the passing grade points "
            "replace the failing grade ('F' = 0 GP) in the cumulative performance calculation."
        ),
        "penalty_cap": (
            "Capped Grade Scenario: The university clears the backlog, but caps the maximum grade point awarded on repeated attempts."
        ),
        "current_attempt_only": (
            "Separate Earned Credit Scenario: Cleared credits are credited in the term cleared."
        )
    }

    return {
        "rule_type": rule_type,
        "rule_description": rule_descriptions.get(rule_type, "Custom University Backlog Rule"),
        "disclaimer": (
            "Note: SPPU and individual engineering colleges periodically update examination ordinances. "
            "Always verify with your controller of examinations whether your branch follows grade replacement "
            "or separate attempt transcript recording."
        ),
        "baseline_cgpa": baseline_cgpa_res["cgpa"],
        "simulated_cgpa_after_clearing": simulated_cgpa,
        "cgpa_boost": delta,
        "total_backlog_credits": round(total_backlog_credits, 2),
        "total_points_gained": round(additional_points, 2),
        "scenarios": cleared_scenarios
    }
