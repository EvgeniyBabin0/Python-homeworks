from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from repository import StudentRepository, get_repo
from models import User

router = APIRouter(prefix="/auth", tags=["auth"])

ACTIVE_SESSIONS: set[int] = set()


class UserRegister(BaseModel):
    username: str


class UserLogin(BaseModel):
    user_id: int


class UserOut(BaseModel):
    id: int
    username: str


@router.post("/register", response_model=UserOut)
def register(
    user_data: UserRegister,
    repo: StudentRepository = Depends(get_repo),
):
    existing = repo.get_user_by_username(user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    user = repo.create_user(user_data.username)
    return UserOut(id=user.id, username=user.username)


@router.post("/login")
def login(
    data: UserLogin,
    repo: StudentRepository = Depends(get_repo),
):
    user = repo.get_user_by_id(data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный идентификатор пользователя")

    ACTIVE_SESSIONS.add(user.id)
    return {"message": "Вход выполнен", "user_id": user.id}


@router.post("/logout")
def logout(
    x_user_id: Annotated[int | None, Header(alias="X-User-Id")] = None,
):
    if x_user_id is None or x_user_id not in ACTIVE_SESSIONS:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    ACTIVE_SESSIONS.discard(x_user_id)
    return {"message": "Выход выполнен"}


def get_current_user(
    repo: StudentRepository = Depends(get_repo),
    x_user_id: Annotated[int | None, Header(alias="X-User-Id")] = None,
) -> User:
    """
    Зависимость для защиты остальных эндпоинтов.
    Требует заголовок X-User-Id и активную сессию.
    """
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Не передан заголовок X-User-Id")

    user = repo.get_user_by_id(x_user_id)
    if not user or x_user_id not in ACTIVE_SESSIONS:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    return user