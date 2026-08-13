from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models import User

client = TestClient(app)


def test_register_login_and_authenticated_me() -> None:
    suffix = uuid4().hex[:10]
    email = f"creator-{suffix}@example.com"
    password = f"creator-ops-{suffix}-secure"
    user_id: str | None = None

    try:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "display_name": "Integration Creator",
                "password": password,
                "timezone": "Asia/Shanghai",
            },
        )
        assert register_response.status_code == 201, register_response.text
        registration = register_response.json()
        assert registration["token_type"] == "bearer"
        assert registration["access_token"]
        assert registration["user"]["email"] == email
        user_id = registration["user"]["id"]

        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {registration['access_token']}"},
        )
        assert me_response.status_code == 200, me_response.text
        assert me_response.json()["id"] == user_id

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email.upper(), "password": password},
        )
        assert login_response.status_code == 200, login_response.text
        assert login_response.json()["user"]["id"] == user_id

        wrong_password_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrong-password"},
        )
        assert wrong_password_response.status_code == 401

    finally:
        if user_id is not None:
            with SessionLocal() as db:
                db.execute(delete(User).where(User.id == user_id))
                db.commit()
