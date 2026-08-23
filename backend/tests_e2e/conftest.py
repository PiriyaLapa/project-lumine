"""
E2E test fixtures — real HTTP against the isolated docker-compose.e2e.yml
stack (real MySQL, real server process). NOT collected by a plain `pytest`
run in backend/ — run explicitly: `pytest backend/tests_e2e`.

Requires the E2E stack up and seeded first:
    docker compose -f docker-compose.e2e.yml up -d
    docker compose -f docker-compose.e2e.yml exec e2e-backend python scripts/seed_e2e_data.py
"""
import os

import httpx
import pytest

E2E_BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:8010")

E2E_STAFF_EMAIL = "e2e@lumine.test"
E2E_STAFF_PASSWORD = "e2e-password-123"


@pytest.fixture(scope="session")
def client() -> httpx.Client:
    with httpx.Client(base_url=E2E_BASE_URL, timeout=10.0) as c:
        yield c


@pytest.fixture(scope="session")
def auth_headers(client: httpx.Client) -> dict:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": E2E_STAFF_EMAIL, "password": E2E_STAFF_PASSWORD},
    )
    assert resp.status_code == 200, (
        f"E2E login failed ({resp.status_code}): {resp.text}. "
        "Did you run scripts/seed_e2e_data.py against the e2e stack?"
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
