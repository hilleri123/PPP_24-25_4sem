from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3

app = FastAPI()

def init_db():
    conn = sqlite3.connect("university.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teacher (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS course (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        student_count INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        FOREIGN KEY (teacher_id) REFERENCES teacher(id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

init_db()

class Teacher(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=100)
    
    class Config:
        orm_mode = True

class Course(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=100)
    student_count: int = Field(..., gt=0)
    teacher_id: int
    
    class Config:
        orm_mode = True

def get_db_connection():
    conn = sqlite3.connect("university.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/teachers", response_model=List[Teacher])
def read_teachers():
    conn = get_db_connection()
    teachers = conn.execute("SELECT * FROM teacher").fetchall()
    conn.close()
    return teachers

@app.post("/teachers", response_model=Teacher, status_code=status.HTTP_201_CREATED)
def create_teacher(name: str = Field(..., min_length=1)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO teacher (name) VALUES (?)", (name,))
    conn.commit()
    teacher_id = cursor.lastrowid
    conn.close()
    return {"id": teacher_id, "name": name}

@app.get("/teachers/{teacher_id}/courses", response_model=List[Course])
def read_teacher_courses(teacher_id: int):
    conn = get_db_connection()
    teacher = conn.execute("SELECT 1 FROM teacher WHERE id = ?", (teacher_id,)).fetchone()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    courses = conn.execute(
        "SELECT * FROM course WHERE teacher_id = ?", 
        (teacher_id,)
    ).fetchall()
    conn.close()
    return courses

@app.delete("/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(teacher_id: int):
    conn = get_db_connection()
    teacher = conn.execute("SELECT 1 FROM teacher WHERE id = ?", (teacher_id,)).fetchone()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    conn.execute("DELETE FROM teacher WHERE id = ?", (teacher_id,))
    conn.commit()
    conn.close()

@app.get("/courses", response_model=List[Course])
def read_courses():
    conn = get_db_connection()
    courses = conn.execute("SELECT * FROM course").fetchall()
    conn.close()
    return courses

@app.post("/courses", response_model=Course, status_code=status.HTTP_201_CREATED)
def create_course(name: str, student_count: int, teacher_id: int):
    conn = get_db_connection()
    teacher = conn.execute("SELECT 1 FROM teacher WHERE id = ?", (teacher_id,)).fetchone()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO course (name, student_count, teacher_id) VALUES (?, ?, ?)",
        (name, student_count, teacher_id)
    )
    conn.commit()
    course_id = cursor.lastrowid
    conn.close()
    return {"id": course_id, "name": name, "student_count": student_count, "teacher_id": teacher_id}

@app.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int):
    conn = get_db_connection()
    course = conn.execute("SELECT 1 FROM course WHERE id = ?", (course_id,)).fetchone()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    conn.execute("DELETE FROM course WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
