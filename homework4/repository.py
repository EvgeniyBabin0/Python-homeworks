# repository.py
import csv
from pathlib import Path
from typing import List

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models import Base, Faculty, Subject, Student, Grade
from db import engine, SessionLocal


class StudentRepository:
    def __init__(self, session: Session):
        self.session = session

    # ---------- INSERT / UPDATE / DELETE базовые операции ----------

    def create_faculty(self, name: str) -> Faculty:
        faculty = Faculty(name=name)
        self.session.add(faculty)
        self.session.commit()
        self.session.refresh(faculty)
        return faculty

    def get_faculty_by_name(self, name: str) -> Faculty | None:
        return self.session.execute(
            select(Faculty).where(Faculty.name == name)
        ).scalar_one_or_none()

    def create_subject(self, name: str) -> Subject:
        subject = Subject(name=name)
        self.session.add(subject)
        self.session.commit()
        self.session.refresh(subject)
        return subject

    def get_subject_by_name(self, name: str) -> Subject | None:
        return self.session.execute(
            select(Subject).where(Subject.name == name)
        ).scalar_one_or_none()

    def create_student(self, last_name: str, first_name: str, faculty_name: str) -> Student:
        faculty = self.get_faculty_by_name(faculty_name)
        if faculty is None:
            faculty = self.create_faculty(faculty_name)

        student = Student(
            last_name=last_name,
            first_name=first_name,
            faculty_id=faculty.id,
        )
        self.session.add(student)
        self.session.commit()
        self.session.refresh(student)
        return student

    def get_student_by_name_and_faculty(
        self, last_name: str, first_name: str, faculty_name: str
    ) -> Student | None:
        faculty = self.get_faculty_by_name(faculty_name)
        if faculty is None:
            return None

        stmt = select(Student).where(
            Student.last_name == last_name,
            Student.first_name == first_name,
            Student.faculty_id == faculty.id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_or_get_student(self, last_name: str, first_name: str, faculty_name: str) -> Student:
        student = self.get_student_by_name_and_faculty(last_name, first_name, faculty_name)
        if student is not None:
            return student
        return self.create_student(last_name, first_name, faculty_name)

    def add_grade(self, student_id: int, subject_name: str, score: int) -> Grade:
        subject = self.get_subject_by_name(subject_name)
        if subject is None:
            subject = self.create_subject(subject_name)

        grade = Grade(
            student_id=student_id,
            subject_id=subject.id,
            score=score,
        )
        self.session.add(grade)
        self.session.commit()
        self.session.refresh(grade)
        return grade

    def update_grade(self, grade_id: int, new_score: int) -> Grade | None:
        grade = self.session.get(Grade, grade_id)
        if grade is None:
            return None
        grade.score = new_score
        self.session.commit()
        self.session.refresh(grade)
        return grade

    def delete_grade(self, grade_id: int) -> bool:
        grade = self.session.get(Grade, grade_id)
        if grade is None:
            return False
        self.session.delete(grade)
        self.session.commit()
        return True

    # ---------- Заполнение БД из students.csv ----------

    def load_from_csv(self, path: str | Path) -> None:
        path = Path(path)
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=",")
            for row in reader:
                last_name = row["Фамилия"].strip()
                first_name = row["Имя"].strip()
                faculty_name = row["Факультет"].strip()
                course_name = row["Курс"].strip()
                score = int(row["Оценка"])

                student = self.create_or_get_student(last_name, first_name, faculty_name)
                self.add_grade(student.id, course_name, score)

    # ---------- Запросы из задания ----------

    def get_students_by_faculty(self, faculty_name: str) -> List[Student]:
        stmt = (
            select(Student)
            .join(Faculty)
            .where(Faculty.name == faculty_name)
            .order_by(Student.last_name, Student.first_name)
        )
        return self.session.execute(stmt).scalars().all()

    def get_unique_courses(self) -> List[str]:
        stmt = select(Subject.name).order_by(Subject.name).distinct()
        return [row[0] for row in self.session.execute(stmt).all()]

    def get_students_by_course_with_low_score(self, course_name: str, threshold: int = 30):
        stmt = (
            select(Student, Grade.score)
            .join(Grade, Grade.student_id == Student.id)
            .join(Subject, Grade.subject_id == Subject.id)
            .where(Subject.name == course_name, Grade.score < threshold)
            .order_by(Grade.score)
        )
        return self.session.execute(stmt).all()

    def get_average_score_by_faculty(self, faculty_name: str) -> float | None:
        stmt = (
            select(func.avg(Grade.score))
            .join(Student, Grade.student_id == Student.id)
            .join(Faculty, Student.faculty_id == Faculty.id)
            .where(Faculty.name == faculty_name)
        )
        result = self.session.execute(stmt).scalar()
        return float(result) if result is not None else None


# вспомогательная функция для контекста
def get_repo() -> StudentRepository:
    db = SessionLocal()
    try:
        yield StudentRepository(db)
    finally:
        db.close()