from app.services.ai_service import ai_service
from app.schemas.notification import AIAnalysisOutput
from fastapi import status


def test_ai_fallback_exam_category():
    """Verify fallback accurately detects Exam category and deadlines."""
    title = "Semester Final Exam Schedule"
    content = "The final examination hall tickets are published. Exams commence from 2026-11-15."
    result = ai_service.analyze_notification(title, content)
    assert isinstance(result, AIAnalysisOutput)
    assert result.category == "Exam"
    assert result.deadline == "2026-11-15"
    assert result.priority in ["High", "Medium"]
    assert len(result.summary) > 0


def test_ai_fallback_placement_category():
    """Verify fallback accurately detects Placement category and high priority."""
    title = "Amazon Campus Recruitment Drive"
    content = "Amazon campus drive registrations are strictly mandatory for all graduating students before 2026-10-05."
    result = ai_service.analyze_notification(title, content)
    assert result.category == "Placement"
    assert result.priority == "High"
    assert result.deadline == "2026-10-05"


def test_ai_fallback_date_formatting():
    """Verify fallback converts DD/MM/YYYY date to ISO YYYY-MM-DD."""
    title = "Tuition Fee Due Date"
    content = "All semester tuition fees must be cleared by 28/09/2026."
    result = ai_service.analyze_notification(title, content)
    assert result.category == "Fees"
    assert result.deadline == "2026-09-28"


def test_ai_fallback_holiday_category():
    """Verify fallback categorizes Holiday and sets low priority."""
    title = "College Holiday Notice"
    content = "The institution will observe a declared holiday on Friday for festival celebrations."
    result = ai_service.analyze_notification(title, content)
    assert result.category == "Holiday"
    assert result.priority == "Low"


def test_ai_fallback_manual_overrides():
    """Verify admin manual overrides take precedence over automatic extraction."""
    title = "Random Title"
    content = "Random text without dates."
    result = ai_service.analyze_notification(
        title=title,
        content=content,
        manual_category="Academic",
        manual_priority="Low",
        manual_deadline="2026-12-31",
    )
    assert result.category == "Academic"
    assert result.priority == "Low"
    assert result.deadline == "2026-12-31"


def test_admin_stats_endpoint(client, admin_headers, student_headers):
    """Test /api/admin/stats returns aggregate metrics."""
    # Student cannot view admin stats
    res_student = client.get("/api/admin/stats", headers=student_headers)
    assert res_student.status_code == status.HTTP_403_FORBIDDEN

    # Admin creates a notification
    client.post(
        "/api/notifications",
        json={"title": "Midterm Exam", "content": "Exam details."},
        headers=admin_headers,
    )

    # Admin views stats
    res_admin = client.get("/api/admin/stats", headers=admin_headers)
    assert res_admin.status_code == status.HTTP_200_OK
    data = res_admin.json()
    assert "total_notifications" in data
    assert data["total_notifications"] >= 1
    assert "total_students" in data
    assert "categories" in data
    assert "priorities" in data
