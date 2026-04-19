from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from repository import StudentRepository, get_repo
from models import Grade, Subject

app = FastAPI(title="Students API")


class GradeCreate(BaseModel):
    student_id: int
    subject_name: str
    score: int


class GradeUpdate(BaseModel):
    score: int


class GradeOut(BaseModel):
    id: int
    student_id: int
    subject_name: str
    score: int


class StudentOut(BaseModel):
    id: int
    last_name: str
    first_name: str
    faculty: str


class LowScoreStudentOut(BaseModel):
    student_id: int
    last_name: str
    first_name: str
    faculty_id: int
    score: int


@app.post("/grades", response_model=GradeOut)
def create_grade(data: GradeCreate, repo: StudentRepository = Depends(get_repo)):
    grade = repo.add_grade(data.student_id, data.subject_name, data.score)
    subject = repo.get_subject_by_name(data.subject_name)

    return GradeOut(
        id=grade.id,
        student_id=grade.student_id,
        subject_name=subject.name if subject else data.subject_name,
        score=grade.score,
    )


@app.get("/grades/{grade_id}", response_model=GradeOut)
def get_grade(grade_id: int, repo: StudentRepository = Depends(get_repo)):
    grade = repo.session.get(Grade, grade_id)
    if grade is None:
        raise HTTPException(status_code=404, detail="Оценка не найдена")

    subject = repo.session.get(Subject, grade.subject_id)

    return GradeOut(
        id=grade.id,
        student_id=grade.student_id,
        subject_name=subject.name if subject else "",
        score=grade.score,
    )


@app.put("/grades/{grade_id}", response_model=GradeOut)
def update_grade(grade