"""
Calculator API routes for SGPA, CGPA, Target GPA, What-If, and Backlog analysis.
"""

from fastapi import APIRouter, HTTPException, status
from ..schemas import (
    SGPACalculateRequest, SGPACalculateResponse,
    CGPACalculateRequest, CGPACalculateResponse,
    TargetGPAPredictRequest, TargetGPAPredictResponse,
    WhatIfRequest, WhatIfResponse,
    BacklogImpactRequest, BacklogImpactResponse
)
from ..calculator import (
    calculate_sgpa,
    calculate_cgpa,
    predict_target_gpa,
    analyze_what_if,
    analyze_backlog_impact,
    CalculationError,
    DEFAULT_SPPU_SCALE
)

router = APIRouter(prefix="/api", tags=["Calculations"])


@router.post("/calculate/sgpa", response_model=SGPACalculateResponse, status_code=status.HTTP_200_OK)
def calculate_sgpa_endpoint(payload: SGPACalculateRequest):
    try:
        subjects_data = [s.model_dump() for s in payload.subjects]
        scheme = payload.custom_scheme if payload.custom_scheme else DEFAULT_SPPU_SCALE
        res = calculate_sgpa(subjects_data, scheme=scheme, max_scale=payload.max_scale or 10.0)
        return res
    except CalculationError as ce:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"SGPA calculation error: {str(e)}")


@router.post("/calculate/cgpa", response_model=CGPACalculateResponse, status_code=status.HTTP_200_OK)
def calculate_cgpa_endpoint(payload: CGPACalculateRequest):
    try:
        semesters_data = [s.model_dump() for s in payload.semesters]
        res = calculate_cgpa(semesters_data, max_scale=payload.max_scale or 10.0)
        return res
    except CalculationError as ce:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"CGPA calculation error: {str(e)}")


@router.post("/predict/target-gpa", response_model=TargetGPAPredictResponse, status_code=status.HTTP_200_OK)
def predict_target_gpa_endpoint(payload: TargetGPAPredictRequest):
    try:
        res = predict_target_gpa(
            current_cgpa=payload.current_cgpa,
            completed_credits=payload.completed_credits,
            remaining_credits=payload.remaining_credits,
            target_cgpa=payload.target_cgpa,
            max_scale=payload.max_scale or 10.0
        )
        return res
    except CalculationError as ce:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Target GPA error: {str(e)}")


@router.post("/analyze/what-if", response_model=WhatIfResponse, status_code=status.HTTP_200_OK)
def analyze_what_if_endpoint(payload: WhatIfRequest):
    try:
        scheme = payload.custom_scheme if payload.custom_scheme else DEFAULT_SPPU_SCALE
        res = analyze_what_if(
            baseline_type=payload.baseline_type,
            baseline_data=payload.baseline_data,
            modifications=payload.modifications,
            scheme=scheme,
            max_scale=payload.max_scale or 10.0
        )
        return res
    except CalculationError as ce:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"What-If error: {str(e)}")


@router.post("/analyze/backlog", response_model=BacklogImpactResponse, status_code=status.HTTP_200_OK)
def analyze_backlog_endpoint(payload: BacklogImpactRequest):
    try:
        semesters_data = [s.model_dump() for s in payload.semesters]
        scheme = payload.custom_scheme if payload.custom_scheme else DEFAULT_SPPU_SCALE
        res = analyze_backlog_impact(
            semesters=semesters_data,
            backlog_subjects=payload.backlog_subjects,
            rule_type=payload.rule_type or "replacement",
            scheme=scheme,
            max_scale=payload.max_scale or 10.0
        )
        return res
    except CalculationError as ce:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Backlog error: {str(e)}")
