"""
SQLite Database module for GPA Calculator AI Agent.
Handles academic history, semesters, calculations, and custom grading schemes.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gpa_academic.db")


def get_db_connection() -> sqlite3.Connection:
    """Creates a database connection with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite database tables and seeds initial sample records."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table: academic_records (semesters & saved calculation snapshots)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academic_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_type TEXT NOT NULL, /* 'semester' or 'calculation' */
            title TEXT NOT NULL,
            semester_num INTEGER,
            sgpa REAL,
            cgpa REAL,
            credits REAL,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Table: grading_schemes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grading_schemes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            scale_max REAL DEFAULT 10.0,
            mapping_json TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()

    # Seed default SPPU grading scheme if not present
    cursor.execute("SELECT id FROM grading_schemes WHERE scheme_id = 'sppu_10'")
    if not cursor.fetchone():
        sppu_mapping = {
            "O": 10.0,
            "A+": 9.0,
            "A": 8.0,
            "B+": 7.0,
            "B": 6.0,
            "C": 5.0,
            "P": 4.0,
            "F": 0.0,
            "Ab": 0.0
        }
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO grading_schemes (scheme_id, name, description, scale_max, mapping_json, is_default, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (
            "sppu_10",
            "SPPU 10-Point CBCS (Engineering)",
            "Savitribai Phule Pune University standard 10-point Choice Based Credit System",
            10.0,
            json.dumps(sppu_mapping),
            now
        ))
        conn.commit()

    # Seed realistic sample engineering academic records if empty
    cursor.execute("SELECT COUNT(*) as count FROM academic_records WHERE record_type = 'semester'")
    count = cursor.fetchone()["count"]
    if count == 0:
        now = datetime.now().isoformat()
        sample_semesters = [
            {
                "record_type": "semester",
                "title": "Semester 1 (FE Sem 1)",
                "semester_num": 1,
                "sgpa": 8.24,
                "credits": 20.0,
                "cgpa": 8.24,
                "data_json": json.dumps({
                    "subjects": [
                        {"name": "Engineering Mathematics I", "credit": 4.0, "grade": "A+", "grade_point": 9.0},
                        {"name": "Engineering Physics", "credit": 4.0, "grade": "A", "grade_point": 8.0},
                        {"name": "Basic Electrical Engineering", "credit": 3.0, "grade": "B+", "grade_point": 7.0},
                        {"name": "Programming & Problem Solving", "credit": 4.0, "grade": "O", "grade_point": 10.0},
                        {"name": "Engineering Graphics", "credit": 3.0, "grade": "A", "grade_point": 8.0},
                        {"name": "Physics & Programming Lab", "credit": 2.0, "grade": "O", "grade_point": 10.0}
                    ],
                    "notes": "Sample FE Semester 1 Record (Clearly marked as sample data)"
                }),
                "created_at": now,
                "updated_at": now
            },
            {
                "record_type": "semester",
                "title": "Semester 2 (FE Sem 2)",
                "semester_num": 2,
                "sgpa": 8.55,
                "credits": 20.0,
                "cgpa": 8.395,
                "data_json": json.dumps({
                    "subjects": [
                        {"name": "Engineering Mathematics II", "credit": 4.0, "grade": "A", "grade_point": 8.0},
                        {"name": "Engineering Chemistry", "credit": 4.0, "grade": "A+", "grade_point": 9.0},
                        {"name": "Basic Electronics Engineering", "credit": 3.0, "grade": "A", "grade_point": 8.0},
                        {"name": "Engineering Mechanics", "credit": 4.0, "grade": "B+", "grade_point": 7.0},
                        {"name": "Workshop Practice", "credit": 2.0, "grade": "O", "grade_point": 10.0},
                        {"name": "Chemistry & Electronics Lab", "credit": 3.0, "grade": "O", "grade_point": 10.0}
                    ],
                    "notes": "Sample FE Semester 2 Record (Clearly marked as sample data)"
                }),
                "created_at": now,
                "updated_at": now
            },
            {
                "record_type": "semester",
                "title": "Semester 3 (SE Sem 1)",
                "semester_num": 3,
                "sgpa": 8.10,
                "credits": 22.0,
                "cgpa": 8.29,
                "data_json": json.dumps({
                    "subjects": [
                        {"name": "Discrete Mathematics", "credit": 4.0, "grade": "A", "grade_point": 8.0},
                        {"name": "Data Structures & Algorithms", "credit": 4.0, "grade": "A+", "grade_point": 9.0},
                        {"name": "Computer Organization & Arch", "credit": 3.0, "grade": "B+", "grade_point": 7.0},
                        {"name": "Digital Electronics & Logic", "credit": 4.0, "grade": "A", "grade_point": 8.0},
                        {"name": "DSA Lab", "credit": 2.0, "grade": "O", "grade_point": 10.0},
                        {"name": "Object Oriented Programming Lab", "credit": 2.0, "grade": "O", "grade_point": 10.0},
                        {"name": "Humanity & Social Science", "credit": 3.0, "grade": "B+", "grade_point": 7.0}
                    ],
                    "notes": "Sample SE Semester 1 Record (Clearly marked as sample data)"
                }),
                "created_at": now,
                "updated_at": now
            },
            {
                "record_type": "semester",
                "title": "Semester 4 (SE Sem 2)",
                "semester_num": 4,
                "sgpa": 8.68,
                "credits": 22.0,
                "cgpa": 8.39,
                "data_json": json.dumps({
                    "subjects": [
                        {"name": "Engineering Mathematics III", "credit": 4.0, "grade": "A+", "grade_point": 9.0},
                        {"name": "Data Base Management Systems", "credit": 4.0, "grade": "O", "grade_point": 10.0},
                        {"name": "Operating Systems", "credit": 4.0, "grade": "A", "grade_point": 8.0},
                        {"name": "Theory of Computation", "credit": 3.0, "grade": "B+", "grade_point": 7.0},
                        {"name": "DBMS & OS Lab", "credit": 3.0, "grade": "O", "grade_point": 10.0},
                        {"name": "Project Based Learning (PBL)", "credit": 4.0, "grade": "A+", "grade_point": 9.0}
                    ],
                    "notes": "Sample SE Semester 2 Record (Clearly marked as sample data)"
                }),
                "created_at": now,
                "updated_at": now
            }
        ]

        for s in sample_semesters:
            cursor.execute("""
                INSERT INTO academic_records 
                (record_type, title, semester_num, sgpa, cgpa, credits, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                s["record_type"], s["title"], s["semester_num"],
                s["sgpa"], s["cgpa"], s["credits"],
                s["data_json"], s["created_at"], s["updated_at"]
            ))
        conn.commit()

    conn.close()


def list_records(record_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves records from the database, sorted by semester_num or created_at."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if record_type:
        cursor.execute(
            "SELECT * FROM academic_records WHERE record_type = ? ORDER BY COALESCE(semester_num, 999), created_at ASC",
            (record_type,)
        )
    else:
        cursor.execute(
            "SELECT * FROM academic_records ORDER BY COALESCE(semester_num, 999), created_at ASC"
        )
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "record_type": r["record_type"],
            "title": r["title"],
            "semester_num": r["semester_num"],
            "sgpa": r["sgpa"],
            "cgpa": r["cgpa"],
            "credits": r["credits"],
            "data": json.loads(r["data_json"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"]
        })
    return results


def get_record_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single record by primary key."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM academic_records WHERE id = ?", (record_id,))
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "id": r["id"],
        "record_type": r["record_type"],
        "title": r["title"],
        "semester_num": r["semester_num"],
        "sgpa": r["sgpa"],
        "cgpa": r["cgpa"],
        "credits": r["credits"],
        "data": json.loads(r["data_json"]),
        "created_at": r["created_at"],
        "updated_at": r["updated_at"]
    }


def insert_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Inserts a new academic record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    data_str = json.dumps(record.get("data", {}))

    cursor.execute("""
        INSERT INTO academic_records 
        (record_type, title, semester_num, sgpa, cgpa, credits, data_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.get("record_type", "semester"),
        record["title"],
        record.get("semester_num"),
        record.get("sgpa"),
        record.get("cgpa"),
        record.get("credits"),
        data_str,
        now,
        now
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return get_record_by_id(new_id)


def update_record(record_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates an existing academic record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM academic_records WHERE id = ?", (record_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return None

    now = datetime.now().isoformat()
    title = updates.get("title", existing["title"])
    semester_num = updates.get("semester_num", existing["semester_num"])
    sgpa = updates.get("sgpa", existing["sgpa"])
    cgpa = updates.get("cgpa", existing["cgpa"])
    credits = updates.get("credits", existing["credits"])
    data_json = json.dumps(updates["data"]) if "data" in updates else existing["data_json"]

    cursor.execute("""
        UPDATE academic_records
        SET title = ?, semester_num = ?, sgpa = ?, cgpa = ?, credits = ?, data_json = ?, updated_at = ?
        WHERE id = ?
    """, (title, semester_num, sgpa, cgpa, credits, data_json, now, record_id))
    conn.commit()
    conn.close()
    return get_record_by_id(record_id)


def delete_record(record_id: int) -> bool:
    """Deletes an academic record by primary key."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM academic_records WHERE id = ?", (record_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def list_schemes() -> List[Dict[str, Any]]:
    """Lists available grading schemes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grading_schemes ORDER BY is_default DESC, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "scheme_id": r["scheme_id"],
            "name": r["name"],
            "description": r["description"],
            "scale_max": r["scale_max"],
            "mapping": json.loads(r["mapping_json"]),
            "is_default": bool(r["is_default"])
        }
        for r in rows
    ]


def save_scheme(scheme_id: str, name: str, description: str, scale_max: float, mapping: Dict[str, float]) -> Dict[str, Any]:
    """Creates or updates a grading scheme."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO grading_schemes (scheme_id, name, description, scale_max, mapping_json, is_default, created_at)
        VALUES (?, ?, ?, ?, ?, 0, ?)
        ON CONFLICT(scheme_id) DO UPDATE SET
            name=excluded.name,
            description=excluded.description,
            scale_max=excluded.scale_max,
            mapping_json=excluded.mapping_json
    """, (scheme_id, name, description, scale_max, json.dumps(mapping), now))
    conn.commit()
    conn.close()
    return {
        "scheme_id": scheme_id,
        "name": name,
        "description": description,
        "scale_max": scale_max,
        "mapping": mapping
    }


# Automatically ensure DB tables exist on import
init_db()
