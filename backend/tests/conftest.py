import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.utils.auth import hash_password, create_access_token

# Use in-memory SQLite database with StaticPool for fast, isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database tables for each test function and roll back afterwards."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    """Fixture that creates and returns an Admin user."""
    user = User(
        name="Admin User",
        email="admin@college.edu",
        password_hash=hash_password("AdminPass123!"),
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user):
    """Authorization headers for Admin user."""
    token = create_access_token(data={"sub": str(admin_user.id), "role": admin_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_user(db_session):
    """Fixture that creates and returns a Student user."""
    user = User(
        name="Student One",
        email="student1@college.edu",
        password_hash=hash_password("StudentPass123!"),
        role="student",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_headers(student_user):
    """Authorization headers for Student user."""
    token = create_access_token(data={"sub": str(student_user.id), "role": student_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_user_two(db_session):
    """Fixture that creates and returns a second Student user."""
    user = User(
        name="Student Two",
        email="student2@college.edu",
        password_hash=hash_password("StudentPass123!"),
        role="student",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_headers_two(student_user_two):
    """Authorization headers for second Student user."""
    token = create_access_token(data={"sub": str(student_user_two.id), "role": student_user_two.role})
    return {"Authorization": f"Bearer {token}"}
