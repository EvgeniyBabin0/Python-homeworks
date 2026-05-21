from homework7.db import SessionLocal
from homework7.repository import StudentRepository

def main():
    db = SessionLocal()
    try:
        repo = StudentRepository(db)
        repo.load_from_csv("students.csv")
    finally:
        db.close()


if __name__ == "__main__":
    main()