from fastapi import status


def test_register_student(client):
    """Test registering a new student account."""
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Jane Student",
            "email": "jane@college.edu",
            "password": "Password123!",
            "role": "student",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "jane@college.edu"
    assert data["user"]["role"] == "student"


def test_register_admin(client):
    """Test registering a new admin account."""
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Prof. Smith",
            "email": "smith@college.edu",
            "password": "AdminPassword123!",
            "role": "admin",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user"]["role"] == "admin"


def test_register_duplicate_email(client):
    """Test that duplicate email registration returns 400."""
    payload = {
        "name": "Duplicate User",
        "email": "dup@college.edu",
        "password": "Password123!",
        "role": "student",
    }
    first_res = client.post("/api/auth/register", json=payload)
    assert first_res.status_code == status.HTTP_201_CREATED

    dup_res = client.post("/api/auth/register", json=payload)
    assert dup_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in dup_res.json()["detail"]


def test_login_success(client, student_user):
    """Test user login with valid credentials."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": student_user.email,
            "password": "StudentPass123!",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == student_user.email


def test_login_invalid_password(client, student_user):
    """Test user login fails with incorrect password."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": student_user.email,
            "password": "WrongPassword!",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_me_authenticated(client, student_headers, student_user):
    """Test /api/auth/me returns the logged in user."""
    response = client.get("/api/auth/me", headers=student_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == student_user.id
    assert data["email"] == student_user.email
    assert data["role"] == student_user.role


def test_get_me_unauthorized(client):
    """Test /api/auth/me without token returns 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
