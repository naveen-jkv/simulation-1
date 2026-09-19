from fastapi import status


def test_admin_create_notification(client, admin_headers):
    """Test that an admin can create a notification and AI fallback extracts metadata."""
    payload = {
        "title": "Placement Training Registration",
        "content": "All final year students must register for placement training before Friday 2026-09-25.",
    }
    response = client.post("/api/notifications", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["category"] == "Placement"
    assert data["priority"] == "High"
    assert data["deadline"] == "2026-09-25"
    assert data["is_read"] is False
    assert "id" in data
    assert "created_at" in data


def test_student_cannot_create_notification(client, student_headers):
    """Test that students are forbidden from creating notifications."""
    payload = {
        "title": "Student Announcement",
        "content": "This should be forbidden.",
    }
    response = client.post("/api/notifications", json=payload, headers=student_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_unauthenticated_cannot_create_notification(client):
    """Test that unauthenticated requests cannot create notifications."""
    response = client.post(
        "/api/notifications",
        json={"title": "Test", "content": "Content"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_notifications_and_filtering(client, admin_headers, student_headers):
    """Test notification listing and query filters (category, priority, search)."""
    # 1. Create Placement notification
    client.post(
        "/api/notifications",
        json={
            "title": "Google Placement Drive",
            "content": "Google campus interview is scheduled on 2026-10-10. Strictly mandatory for CS students.",
        },
        headers=admin_headers,
    )
    # 2. Create Exam notification
    client.post(
        "/api/notifications",
        json={
            "title": "Midterm Examination Schedule",
            "content": "The midterm exam hall tickets are released for download.",
        },
        headers=admin_headers,
    )
    # 3. Create Holiday notification
    client.post(
        "/api/notifications",
        json={
            "title": "National Holiday Declaration",
            "content": "The college will remain closed on Monday on account of public holiday.",
        },
        headers=admin_headers,
    )

    # Test listing all (should have 3)
    res_all = client.get("/api/notifications", headers=student_headers)
    assert res_all.status_code == status.HTTP_200_OK
    assert len(res_all.json()) == 3

    # Test category filter: category=exam
    res_cat = client.get("/api/notifications?category=exam", headers=student_headers)
    assert res_cat.status_code == status.HTTP_200_OK
    items_cat = res_cat.json()
    assert len(items_cat) == 1
    assert items_cat[0]["category"] == "Exam"

    # Test search filter: search=Google
    res_search = client.get("/api/notifications?search=Google", headers=student_headers)
    assert res_search.status_code == status.HTTP_200_OK
    items_search = res_search.json()
    assert len(items_search) == 1
    assert "Google" in items_search[0]["title"]


def test_read_tracking_and_isolation(
    client, admin_headers, student_headers, student_headers_two
):
    """
    Test read/unread tracking and ensure isolation:
    When Student 1 marks notification as read, Student 2 still sees it as unread.
    """
    # Admin creates a notification
    res_create = client.post(
        "/api/notifications",
        json={
            "title": "Library Book Return",
            "content": "Please return all borrowed books before 2026-09-30.",
        },
        headers=admin_headers,
    )
    notif_id = res_create.json()["id"]

    # Student 1 checks: should be unread
    res_s1_init = client.get(f"/api/notifications/{notif_id}", headers=student_headers)
    assert res_s1_init.status_code == status.HTTP_200_OK
    assert res_s1_init.json()["is_read"] is False

    # Student 1 marks as read
    res_read = client.put(f"/api/notifications/{notif_id}/read", headers=student_headers)
    assert res_read.status_code == status.HTTP_200_OK
    assert res_read.json()["is_read"] is True

    # Student 1 checks again: is_read is True
    res_s1_after = client.get(f"/api/notifications/{notif_id}", headers=student_headers)
    assert res_s1_after.json()["is_read"] is True

    # Student 2 checks: MUST STILL BE UNREAD for Student 2!
    res_s2 = client.get(f"/api/notifications/{notif_id}", headers=student_headers_two)
    assert res_s2.json()["is_read"] is False

    # Student 1 filters by is_read=true
    res_filter_read = client.get("/api/notifications?is_read=true", headers=student_headers)
    assert len(res_filter_read.json()) == 1

    # Student 2 filters by is_read=true (should be 0)
    res_filter_s2 = client.get("/api/notifications?is_read=true", headers=student_headers_two)
    assert len(res_filter_s2.json()) == 0


def test_admin_update_and_delete_notification(client, admin_headers, student_headers):
    """Test admin update and delete endpoints."""
    # Create notification
    res_create = client.post(
        "/api/notifications",
        json={"title": "Original Title", "content": "Original announcement text."},
        headers=admin_headers,
    )
    notif_id = res_create.json()["id"]

    # Student cannot update
    res_student_update = client.put(
        f"/api/notifications/{notif_id}",
        json={"title": "Hacked Title"},
        headers=student_headers,
    )
    assert res_student_update.status_code == status.HTTP_403_FORBIDDEN

    # Admin updates
    res_admin_update = client.put(
        f"/api/notifications/{notif_id}",
        json={"title": "Updated Title", "priority": "High"},
        headers=admin_headers,
    )
    assert res_admin_update.status_code == status.HTTP_200_OK
    assert res_admin_update.json()["title"] == "Updated Title"
    assert res_admin_update.json()["priority"] == "High"

    # Student cannot delete
    res_student_del = client.delete(
        f"/api/notifications/{notif_id}",
        headers=student_headers,
    )
    assert res_student_del.status_code == status.HTTP_403_FORBIDDEN

    # Admin deletes
    res_admin_del = client.delete(
        f"/api/notifications/{notif_id}",
        headers=admin_headers,
    )
    assert res_admin_del.status_code == status.HTTP_200_OK

    # Verify 404 after deletion
    res_get = client.get(f"/api/notifications/{notif_id}")
    assert res_get.status_code == status.HTTP_404_NOT_FOUND
