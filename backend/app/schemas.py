"""
Pydantic Schemas for API requests, responses, and validation.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator


class SubjectInput(BaseModel):
    name: str = Field(..., min_length=1, description="Subject or course name")
    code: Optional[str] = Field(None, description="Course/Subject code (e.g., CS301)")
    credit: float = Field(..., gt=0, description="Credits assigned to the subject (strictly > 0)")
    grade: Optional[str] = Field(None, description="Letter grade (e.g., O, A+, A, B+, B, C, P, F)")
    grade_point: Optional[float] = Field(None, ge=0, description="Numerical grade point (0.0 to 10.0)")

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Subject name cannot be empty")
        return s


class SGPACalculateRequest(BaseModel):
    subjects: List[SubjectInput] = Field(..., min_length=1, description="List of subjects")
    scheme_name: Optional[str] = Field("sppu_10", description="Grading scheme identifier")
    custom_scheme: Optional[Dict[str, float]] = Field(None, description="Custom letter-grade to grade-point mapping")
    max_scale: Optional[float] = Field(10.0, gt=0, le=100.0, description="Maximum grade scale (default 10.0)")


class SGPACalculateResponse(BaseModel):
    sgpa: float
    sgpa_exact: float
    total_credits: float
    total_weighted_points: float
    subject_count: int
    subjects: List[Dict[str, Any]]
    has_backlog: bool
    formula: str


class SemesterInput(BaseModel):
    name: str = Field(..., min_length=1, description="Semester title (e.g., Semester 1)")
    sgpa: float = Field(..., ge=0, description="Earned SGPA in this semester")
    credits: float = Field(..., gt=0, description="Earned / applicable credits for this semester")

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Semester name cannot be empty")
        return s


class CGPACalculateRequest(BaseModel):
    semesters: List[SemesterInput] = Field(..., min_length=1, description="List of completed semesters")
    max_scale: Optional[float] = Field(10.0, gt=0, le=100.0, description="Maximum scale (default 10.0)")


class CGPACalculateResponse(BaseModel):
    cgpa: float
    cgpa_exact: float
    simple_average: float
    difference_from_simple_average: float
    total_credits: float
    total_weighted_points: float
    semester_count: int
    semesters: List[Dict[str, Any]]
    formula: str
    explanation: str


class TargetGPAPredictRequest(BaseModel):
    current_cgpa: float = Field(..., ge=0, description="Current cumulative GPA")
    completed_credits: float = Field(..., ge=0, description="Total credits completed so far")
    remaining_credits: float = Field(..., gt=0, description="Total credits remaining in future semesters")
    target_cgpa: float = Field(..., ge=0, description="Desired graduation CGPA")
    max_scale: Optional[float] = Field(10.0, gt=0, le=100.0, description="Maximum scale (default 10.0)")


class TargetGPAPredictResponse(BaseModel):
    achievable: bool
    status: str
    required_sgpa: float
    required_sgpa_exact: float
    target_cgpa: float
    current_cgpa: float
    completed_credits: float
    remaining_credits: float
    total_credits: float
    max_scale: float
    max_achievable_cgpa: float
    message: str
    scenarios: List[Dict[str, Any]]


class WhatIfRequest(BaseModel):
    baseline_type: str = Field(..., description="'sgpa' or 'cgpa'")
    baseline_data: Dict[str, Any] = Field(..., description="Baseline subject or semester data")
    modifications: List[Dict[str, Any]] = Field(..., description="Hypothetical modifications or additions")
    scheme_name: Optional[str] = Field("sppu_10", description="Grading scheme")
    custom_scheme: Optional[Dict[str, float]] = Field(None, description="Custom scheme mapping")
    max_scale: Optional[float] = Field(10.0, gt=0, description="Maximum scale")


class WhatIfResponse(BaseModel):
    type: str
    baseline_score: float
    simulated_score: float
    delta: float
    delta_direction: str
    baseline_details: Dict[str, Any]
    simulated_details: Dict[str, Any]
    label: str


class BacklogImpactRequest(BaseModel):
    semesters: List[SemesterInput] = Field(..., min_length=1, description="Historical semesters")
    backlog_subjects: List[Dict[str, Any]] = Field(..., min_length=1, description="Backlog subjects to clear")
    rule_type: Optional[str] = Field("replacement", description="Rule: replacement, penalty_cap, current_attempt_only")
    scheme_name: Optional[str] = Field("sppu_10")
    custom_scheme: Optional[Dict[str, float]] = None
    max_scale: Optional[float] = Field(10.0, gt=0)


class BacklogImpactResponse(BaseModel):
    rule_type: str
    rule_description: str
    disclaimer: str
    baseline_cgpa: float
    simulated_cgpa_after_clearing: float
    cgpa_boost: float
    total_backlog_credits: float
    total_points_gained: float
    scenarios: List[Dict[str, Any]]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Student's query or statement")
    conversation_id: Optional[str] = Field(None, description="Optional thread/session ID")
    academic_context: Optional[Dict[str, Any]] = Field(None, description="Current user grades, CGPA, or semester data")


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    intent: str
    calculations_performed: Optional[List[Dict[str, Any]]] = None
    sources: Optional[List[str]] = None


class AcademicRecordCreate(BaseModel):
    record_type: str = Field(..., description="'semester' or 'saved_calculation'")
    title: str = Field(..., min_length=1)
    semester_num: Optional[int] = Field(None, ge=1, le=12)
    sgpa: Optional[float] = Field(None, ge=0)
    cgpa: Optional[float] = Field(None, ge=0)
    credits: Optional[float] = Field(None, gt=0)
    data: Dict[str, Any] = Field(default_factory=dict, description="Detailed JSON data")


class AcademicRecordUpdate(BaseModel):
    title: Optional[str] = None
    semester_num: Optional[int] = None
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    credits: Optional[float] = None
    data: Optional[Dict[str, Any]] = None


class AcademicRecordResponse(BaseModel):
    id: int
    record_type: str
    title: str
    semester_num: Optional[int] = None
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    credits: Optional[float] = None
    data: Dict[str, Any]
    created_at: str
    updated_at: str
