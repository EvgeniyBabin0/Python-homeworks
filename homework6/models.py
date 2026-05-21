from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass



class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"User(id={self.id}, username='{self.username}')"



class Faculty(Base):
    __tablename__ = "faculties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    students: Mapped[list["Student"]] = relationship(back_populates="faculty")

    def __repr__(self) -> str:
        return f"Faculty(id={self.id}, name='{self.name}')"



class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    grades: Mapped[list["Grade"]] = relationship(back_populates="subject")

    def __repr__(self) -> str:
        return f"Subject(id={self.id}, name='{self.name}')"




class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"), nullable=False)

    faculty: Mapped["Faculty"] = relationship(back_populates="students")
    grades: Mapped[list["Grade"]] = relationship(back_populates="student")

    __table_args__ = (
        UniqueConstraint("last_name", "first_name", "faculty_id", name="uq_student_fullname_faculty"),
    )

    def __repr__(self) -> str:
        return (
            f"Student(id={self.id}, last_name='{self.last_name}', "
            f"first_name='{self.first_name}', faculty_id={self.faculty_id})"
        )



class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)

    student: Mapped["Student"] = relationship(back_populates="grades")
    subject: Mapped["Subject"] = relationship(back_populates="grades")

    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="check_score_range"),
    )

    def __repr__(self) -> str:
        return (
            f"Grade(id={self.id}, student_id={self.student_id}, "
            f"subject_id={self.subject_id}, score={self.score})"
        )