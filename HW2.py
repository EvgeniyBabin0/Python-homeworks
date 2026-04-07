import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator, model_validator


class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    real_name: str
    email: EmailStr
    phone: str
    password: str
    password_confirm: str = Field(exclude=True)
    age: int = Field(..., ge=18, le=120)
    registration_date: datetime = Field(default_factory=datetime.now)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not re.fullmatch(r"^[a-zA-Z0-9_]{3,20}$", value):
            raise ValueError(
                "Имя пользователя должно содержать от 3 до 20 символов и только латинские буквы, цифры и подчёркивание"
            )
        return value

    @field_validator("real_name")
    @classmethod
    def validate_real_name(cls, value: str) -> str:
        if len(value.strip()) < 2:
            raise ValueError("Реальное имя должно содержать минимум 2 символа")
        if not value[0].isupper():
            raise ValueError("Реальное имя должно начинаться с заглавной буквы")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.fullmatch(r"^\+\d-\d{3}-\d{2}-\d{2}$", value):
            raise ValueError("Номер телефона должен быть в формате +X-XXX-XX-XX")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if not re.search(r"\d", value):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        return value

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Пароли не совпадают")
        return self


def register_user(data: dict):
    try:
        user = UserRegistration.model_validate(data)
        return user
    except ValidationError as e:
        return [
            {
                "field": ".".join(str(x) for x in err["loc"]),
                "message": err["msg"]
            }
            for err in e.errors()
        ]