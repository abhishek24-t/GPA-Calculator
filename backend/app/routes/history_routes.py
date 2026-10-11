"""
Academic records and history API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from ..schemas import AcademicRecordCreate, AcademicRecordUpdate, AcademicRecordResponse
from ..database import (
    list_records,
    get_record_by_id,
    insert_record,
    update_record,
    delete_record,
    list_schemes,
    save_scheme
)

router = APIRouter(prefix="/api", tags=["History & Records"])


@router.get("/history", response_model=List[AcademicRecordResponse])
def get_history(record_type: Optional[str] = Query(None, description="'semester' or 'saved_calculation'")):
    return list_records(record_type=record_type)


@router.post("/history", response_model=AcademicRecordResponse, status_code=status.HTTP_201_CREATED)
def create_history_record(payload: AcademicRecordCreate):
    record = insert_record(payload.model_dump())
    if not record:
        raise HTTPException(status_code=500, detail="Failed to save academic record.")
    return record


@router.get("/history/{record_id}", response_model=AcademicRecordResponse)
def get_single_record(record_id: int):
    rec = get_record_by_id(record_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Academic record #{record_id} not found.")
    return rec


@router.put("/history/{record_id}", response_model=AcademicRecordResponse)
def update_history_record(record_id: int, payload: AcademicRecordUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated = update_record(record_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Academic record #{record_id} not found.")
    return updated


@router.delete("/history/{record_id}", status_code=status.HTTP_200_OK)
def delete_history_record(record_id: int):
    deleted = delete_record(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Academic record #{record_id} not found.")
    return {"message": f"Academic record #{record_id} deleted successfully.", "success": True}


@router.get("/schemes")
def get_grading_schemes():
    return list_schemes()


@router.post("/schemes")
def create_or_update_scheme(payload: dict):
    scheme_id = payload.get("scheme_id")
    name = payload.get("name")
    if not scheme_id or not name:
        raise HTTPException(status_code=400, detail="scheme_id and name are required.")
    return save_scheme(
        scheme_id=scheme_id,
        name=name,
        description=payload.get("description", ""),
        scale_max=payload.get("scale_max", 10.0),
        mapping=payload.get("mapping", {})
    )
