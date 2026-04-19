from db import SessionLocal
from repository import StudentRepository

def main():
    db = SessionLocal()
    try:
        repo = StudentRepository(db)
        repo.load_from_csv("students.csv")
    finally:
        db.close()


if __name__ == "__main__":
    main()