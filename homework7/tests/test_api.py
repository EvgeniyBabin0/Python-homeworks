import uuid


def register_and_login(client, username: str = "test_user"):
    reg_response = client.post("/auth/register", json={"username": username})

    if reg_response.status_code == 200:
        user_id = reg_response.json()["id"]
    elif reg_response.status_code == 400:
        username = f"{username}_{uuid.uuid4().hex[:6]}"
        reg_response = client.post("/auth/register", json={"username": username})
        user_id = reg_response.json()["id"]
    else:
        raise AssertionError(f"Unexpected register status: {reg_response.status_code}")

    login_response = client.post("/auth/login", json={"user_id": user_id})
    assert login_response.status_code == 200
    return user_id


def test_register_success(client):
    username = f"user_{uuid.uuid4().hex[:6]}"
    response = client.post("/auth/register", json={"username": username})

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["username"] == username


def test_register_duplicate_user(client):
    username = f"user_{uuid.uuid4().hex[:6]}"
    first = client.post("/auth/register", json={"username": username})
    second = client.post("/auth/register", json={"username": username})

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"] == "Пользователь уже существует"


def test_login_success(client):
    user_id = register_and_login(client, "login_success_user")
    response = client.post("/auth/login", json={"user_id": user_id})

    assert response.status_code == 200
    assert response.json()["user_id"] == user_id


def test_login_invalid_user(client):
    response = client.post("/auth/login", json={"user_id": 999999})

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный идентификатор пользователя"


def test_logout_success(client):
    user_id = register_and_login(client, "logout_success_user")
    response = client.post("/auth/logout", headers={"X-User-Id": str(user_id)})

    assert response.status_code == 200
    assert response.json()["message"] == "Выход выполнен"


def test_logout_without_auth(client):
    response = client.post("/auth/logout")

    assert response.status_code == 401
    assert response.json()["detail"] == "Пользователь не авторизован"


def test_get_courses_unauthorized(client):
    response = client.get("/courses")
    assert response.status_code == 401


def test_get_courses_authorized(client):
    user_id = register_and_login(client, "courses_user")
    response = client.get("/courses", headers={"X-User-Id": str(user_id)})

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_average_score_unauthorized(client):
    response = client.get("/faculties/АВТФ/average_score")
    assert response.status_code == 401


def test_average_score_authorized(client):
    user_id = register_and_login(client, "avg_user")
    response = client.get(
        "/faculties/АВТФ/average_score",
        headers={"X-User-Id": str(user_id)}
    )

    assert response.status_code in (200, 404)