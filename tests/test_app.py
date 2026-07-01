def create_user(client):
    response = client.post(
        "/users",
        json={"name": "Mayank", "email": "mayank@example.com", "password_hash": "hashed"},
    )
    assert response.status_code == 200
    return response.json()["data"]


def create_project(client, user_id: str):
    response = client.post(
        "/projects",
        json={"user_id": user_id, "name": "Laptop Scraper", "description": "Collect listings"},
    )
    assert response.status_code == 200
    return response.json()["data"]


def create_conversation(client, project_id: str, user_id: str):
    response = client.post(
        "/conversations",
        json={"project_id": project_id, "user_id": user_id, "title": "Discovery chat"},
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "ScrapeFlow context service running"
    assert body["data"]["status"] == "ok"


def test_create_user(client):
    user = create_user(client)
    assert user["name"] == "Mayank"
    assert user["email"] == "mayank@example.com"


def test_create_project_and_auto_context(client):
    user = create_user(client)
    project = create_project(client, user["id"])
    context_response = client.get(f"/projects/{project['id']}/context")
    assert context_response.status_code == 200
    context = context_response.json()["data"]
    assert context["project_id"] == project["id"]
    assert context["fields"] == []
    assert context["filters"] == []
    assert context["version"] == 1


def test_create_conversation(client):
    user = create_user(client)
    project = create_project(client, user["id"])
    conversation = create_conversation(client, project["id"], user["id"])
    assert conversation["project_id"] == project["id"]
    assert conversation["user_id"] == user["id"]


def test_post_message_updates_context(client):
    user = create_user(client)
    project = create_project(client, user["id"])
    conversation = create_conversation(client, project["id"], user["id"])

    response = client.post(
        f"/conversations/{conversation['id']}/messages",
        json={
            "role": "user",
            "content": "extract laptops from https://example.com and include price and rating and export as excel",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["message"]["content"].startswith("extract laptops")
    assert payload["context"]["target_url"] == "https://example.com"
    assert payload["context"]["domain"] == "example.com"
    assert payload["context"]["export_format"] == "excel"
    assert "price" in payload["context"]["fields"]
    assert "rating" in payload["context"]["fields"]
    assert payload["context"]["entity"] == "laptops"
    assert payload["context"]["version"] == 2


def test_get_project_context(client):
    user = create_user(client)
    project = create_project(client, user["id"])
    response = client.get(f"/projects/{project['id']}/context")
    assert response.status_code == 200
    assert response.json()["data"]["project_id"] == project["id"]


def test_create_job(client):
    user = create_user(client)
    project = create_project(client, user["id"])
    response = client.post("/jobs", json={"project_id": project["id"], "job_type": "extraction"})
    assert response.status_code == 200
    job = response.json()["data"]
    assert job["project_id"] == project["id"]
    assert job["status"] == "created"


def test_update_job_status(client):
    user = create_user(client)
    project = create_project(client, user["id"])
    create_response = client.post("/jobs", json={"project_id": project["id"]})
    job_id = create_response.json()["data"]["id"]

    response = client.patch(f"/jobs/{job_id}", json={"status": "running"})
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "running"

def test_root_ui(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "ScrapeFlow Test Console" in response.text
