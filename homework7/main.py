from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from homework7.repository import StudentRepository, get_repo
from homework7.auth_router import router as auth_router, get_current_user
from homework7.db import SessionLocal
from homework7.cache import get_cache, set_cache, clear_all_app_cache

app = FastAPI(title="Students API with Auth, BackgroundTasks and Redis Cache")
app.include_router(auth_router)


# ---------- Pydantic схемы ----------

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


class LoadCsvRequest(BaseModel):
    file_path: str


class DeleteGradesRequest(BaseModel):
    grade_ids: list[int]


# ---------- Background tasks ----------

def background_load_csv(file_path: str):
    db = SessionLocal()
    try:
        repo = StudentRepository(db)
        repo.load_from_csv(file_path)
        clear_all_app_cache()
    finally:
        db.close()


def background_delete_grades(grade_ids: list[int]):
    db = SessionLocal()
    try:
        repo = StudentRepository(db)
        repo.delete_grades_by_ids(grade_ids)
        clear_all_app_cache()
    finally:
        db.close()


# ---------- CRUD по оценкам ----------

@app.post("/grades", response_model=GradeOut)
def create_grade(
    data: GradeCreate,
    repo: StudentRepository = Depends(get_repo),
    _: object = Depends(get_current_user),
):
    grade = repo.add_grade(data.student_id, data.subject_name, data.score)
    clear_all_app_cache()
    return GradeOut(
        id=grade.id,
        student_id=grade.student_id,
        subject_name=data.subject_name,
        score=grade.score,
    )


@app.get("/grades/{grade_id}", response_model=GradeOut)
def get_grade(
    grade_id: int,
    repo: StudentRepository = Depends(get_repo),
    _: object = Depends(get_current_user),
):
    cache_key = f"grade:{grade_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    grade = repo.get_grade(grade_id)
    if grade is None:
        raise HTTPException(status_code=404, detail="Оценка не найдена")

    subject = repo.session.get(type(grade.subject), grade.subject_id) if grade.subject else None
    result = GradeOut(
        id=grade.id,
        student_id=grade.student_id,
        subject_name=subject.name if subject else "",
        score=grade.score,
    ).model_dump()

    set_cache(cache_key, result)
    return result


@app.put("/grades/{grade_id}", response_model=GradeOut)
def update_grade(
    grade_id: int,
    data: GradeUpdate,
    repo: StudentRepository = Depends(get_repo),
    _: object = Depends(get_current_user),
):
    grade = repo.update_grade(grade_id, data.score)
    if grade is None:
        raise HTTPException(status_code=404, detail="Оценка не найдена")

    clear_all_app_cache()
    subject_name = grade.subject.name if grade.subject else ""
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
    _: object = Depends(get_current_user),
):
    ok = repo.delete_grade(grade_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Оценка не найдена")

    clear_all_app_cache()
    return {"status": "deleted"}


# ---------- Background endpoints ----------

@app.post("/tasks/load-csv")
def load_csv_in_background(
    data: LoadCsvRequest,
    background_tasks: BackgroundTasks,
    _: object = Depends(get_current_user),
):
    if not Path(data.file_path).exists():
        raise HTTPException(status_code=404, detail="CSV-файл не найден")

    background_tasks.add_task(background_load_csv, data.file_path)
    return {"message": "Загрузка CSV запущена в фоне", "file_path": data.file_path}


@app.delete("/tasks/delete-grades")
def delete_grades_in_background(
    data: DeleteGradesRequest,
    background_tasks: BackgroundTasks,
    _: object = Depends(get_current_user),
):
    if not data.grade_ids:
        raise HTTPException(status_code=400, detail="Список grade_ids пуст")

    background_tasks.add_task(background_delete_grades, data.grade_ids)
    return {"message": "Удаление оценок запущено в фоне", "grade_ids": data.grade_ids}


# ---------- GET endpoints with cache ----------

@app.get("/faculties/{faculty_name}/students", response_model=list[StudentOut])
def students_by_faculty(
    faculty_name: str,
    repo: StudentRepository = Depends(get_repo),
    _: object = Depends(get_current_user),
):
    cache_key = f"faculty_students:{faculty_name}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    students = repo.get_students_by_faculty(faculty_name)
    result = [
        StudentOut(
            id=s.id,
            last_name=s.last_name,
            first_name=s.first_name,
            faculty=faculty_name,
        ).model_dump()
        for s in students
    ]

    set_cache(cache_key, result)
    return result


@app.get("/courses", response_model=list[str])
def unique_courses(
    repo: StudentRepository = Depends(get_repo),
    _: object = Depends(get_current_user),
):
    cache_key = "courses:all"
    cached = get_cache(cache_key)
    if cached:
        return cached

    result = repo.get_unique_courses()
    set_cache(cache_key, result)
    return result


@app.get("/courses/{course_name}/students_low")
def students_by_course_low(
    course_name: str,
    repo: StudentRepository = Depends(get_repo),
    _: object = Depends(get_current_user),
):
    cache_key = f"course_low:{course_name}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    rows = repo.get_students_by_course_with_low_score(course_name, threshold=30)
    result = [
        {
            "student_id": student.id,
            "last_name": student.last_name,
            "first_name": student.first_name,
            "faculty_id": student.faculty_id,
            "score": score,
        }
        for student, score in rows
    ]

    set_cache(cache_key, result)
    return result


@app.get("/faculties/{faculty_name}/average_score")
def average_score_by_faculty(
    faculty_name: str,
    repo: StudentRepository = Depends(get_repo),
    _: object = Depends(get_current_user),
):
    cache_key = f"faculty_avg:{faculty_name}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    avg_score = repo.get_average_score_by_faculty(faculty_name)
    if avg_score is None:
        raise HTTPException(status_code=404, detail="Нет оценок для этого факультета")

    result = {"faculty": faculty_name, "average_score": avg_score}
    set_cache(cache_key, result)
    return result