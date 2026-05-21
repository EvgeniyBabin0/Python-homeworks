import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from homework7.main import app
from homework7.models import Base
from homework7.repository import get_repo, StudentRepository

TEST_DB = "sqlite:///./test_homework7.db"

engine = create_engine(
    TEST_DB,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_repo():
    db = TestingSessionLocal()
    try:
        yield StudentRepository(db)
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    app.dependency_overrides[get_repo] = override_get_repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()