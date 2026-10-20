from copy import deepcopy
from importlib import import_module

import pytest
from fastapi.testclient import TestClient


app_module = import_module("src.app")
ACTIVITY_NAME = "Chess Club"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_app(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activity = response.json()[ACTIVITY_NAME]
    assert activity["description"]
    assert isinstance(activity["participants"], list)


def test_signup_adds_participant(client):
    email = "new-student@mergington.edu"

    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY_NAME}"}
    assert email in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    email = "existing-student@mergington.edu"
    app_module.activities[ACTIVITY_NAME]["participants"].append(email)

    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities[ACTIVITY_NAME]["participants"].count(email) == 1


def test_delete_removes_participant(client):
    email = "student-to-remove@mergington.edu"
    app_module.activities[ACTIVITY_NAME]["participants"].append(email)

    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {ACTIVITY_NAME}"}
    assert email not in app_module.activities[ACTIVITY_NAME]["participants"]


def test_delete_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Activity/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_delete_rejects_unregistered_participant(client):
    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/participants",
        params={"email": "not-registered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"