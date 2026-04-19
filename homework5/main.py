from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from repository import StudentRepository, get_repo
from auth_router import router as auth_router, get_current_user


app = FastAPI(title="Students API with Auth")

app.include_router(auth_router)



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



@app.post("/grades", response_model=GradeOut)
def create_grade(
    data: GradeCreate,
    repo: StudentRepository = Depends(get_repo),
    user=Depends(get_current_user),
):
    grade = repo.add_grade(data.student_id, data.subject_name, data.score)
    subject = repo.get_subject_by_name(data.subject_name)
    return GradeOut(
        id=grade.id,
        student_id=grade.student_id,
        subject_name=subject.name if subject else data.subject_name,
        score=grade.score,
    )


@app.get("/grades/{grade_id}", response_model=GradeOut)
def get_grade(
    grade_id: int,
    repo: StudentRepository = Depends(get_repo),
    user=Depends(get_current_user),
):
    grade = repo.get_grade(grade_id)
    if grade is None:
        raise HTTPException(status_code=404, detail="Оценка не найдена")

    subject = repo.session.get(type(repo.get_subject_by_name).__annotations__.get("return", None), grade.subject_id)  # если сложно, можно заменить на прямой запрос
    if subject is None:
        subject_name = ""
    else:
        subject_name = subject.name

    return GradeOut(
        id=grade.id,
        student_id=grade.student_id,
        subject_name=subject_name,
        score=grade.score,
    )


@app.put("/grades/{grade_id}", response_model=GradeOut)
def update_grade(
    grade_id: int,
    data: GradeUpdate,
    repo: StudentRepository = Depends(get_repo),
    user=Depends(get_current_user),
):
    grade = repo.update_grade(grade_id, data.score)
    if grade is None:
        raise HTTPException(status_code=404, detail="Оценка не найдена")

    subject = repo.session.get(type(repo.get_subject_by_name).__annotations__.get("return", None), grade.subject_id)
    subject_name = subject.name if subject else ""
    return GradeOut(
        id=grade.id,
        student_id=grade.student_id,
        subject_name=subject_name,
        score=grade.score,
    )


@app.delete("/grades/{grade_id}")
def delete_grade(
    grade_id: int,
    repo: StudentRepository = Depends(get_repo),
    user=Depends(get_current_user),
):
    ok = repo.delete_grade(grade_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Оценка не найдена")
    return {"status": "deleted"}



@app.get("/faculties/{faculty_name}/students", response_model=list[StudentOut])
def students_by_faculty(
    faculty_name: str,
    repo: StudentRepository = Depends(get_repo),
    user=Depends(get_current_user),
):
    students = repo.get_students_by_faculty(faculty_name)
    return [
        StudentOut(
            id=s.id,
            last_name=s.last_name,
            first_name=s.first_name,
            faculty=faculty_name,
        )
        for s in students
    ]


@app.get("/courses", response_model=list[str])
def unique_courses(
    repo: StudentRepository = Depends(get_repo),
    user=Depends(get_current_user),
):
    return repo.get_unique_courses()


@app.get("/courses/{course_name}/students_low")
def students_by_course_low(
    course_name: str,
    repo: StudentRepository = Depends(get_repo),
    user=Depends(get_current_user),
):
    rows = repo.get_students_by_course_with_low_score(course_name, threshold=30)
    return [
        {
            "student_id": student.id,
            "last_name": student.last_name,
            "first_name": student.first_name,
            "faculty_id": student.faculty_id,
            "score": score,
        }
        for student, score in rows
    ]


@app.get("/faculties/{faculty_name}/average_score")
def average_score_by_faculty(
    faculty_name: str,
    repo: StudentRepository = Depends(get_repo),
    user=Depends(get_current_user),
):
    avg_score = repo.get_average_score_by_faculty(faculty_name)
    if avg_score is None:
        raise HTTPException(status_code=404, detail="Нет оценок для этого факультета")
    return {"faculty": faculty_name, "average_score": avg_score}