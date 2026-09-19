import json
import logging
import re
from typing import Optional
from openai import OpenAI
from app.config import settings
from app.schemas.notification import AIAnalysisOutput, NotificationCategory, NotificationPriority

logger = logging.getLogger("ai_service")


class AIService:
    """
    OpenAI-compatible AI service for analyzing college notifications:
    - Summarizes announcements
    - Categorizes into allowed taxonomy
    - Determines priority based on urgency
    - Extracts deadlines
    - Provides resilient rule-based heuristic fallback if AI API is unreachable or fails
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY.strip() if settings.OPENAI_API_KEY else ""
        self.base_url = settings.OPENAI_BASE_URL.strip() if settings.OPENAI_BASE_URL else None
        self.model = settings.OPENAI_MODEL.strip() if settings.OPENAI_MODEL else "gpt-4o-mini"

    def _is_api_configured(self) -> bool:
        """Check if a real API key is configured."""
        if not self.api_key:
            return False
        # Filter out common placeholders
        if any(self.api_key.lower().startswith(prefix) for prefix in ("dummy", "your_", "sk-your", "<")):
            return False
        return True

    def analyze_notification(
        self,
        title: str,
        content: str,
        manual_category: Optional[str] = None,
        manual_priority: Optional[str] = None,
        manual_deadline: Optional[str] = None,
    ) -> AIAnalysisOutput:
        """
        Analyze notification text using the AI provider, or fall back to heuristics
        if the AI service fails or is not configured.
        """
        if self._is_api_configured():
            try:
                client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url if self.base_url else "https://api.openai.com/v1",
                )

                system_prompt = (
                    "You are an expert AI assistant for a College Notification Hub.\n"
                    "Analyze the given college announcement and return a structured JSON response with:\n"
                    "- 'summary': A clear, concise 1-2 sentence executive summary (max 200 characters).\n"
                    "- 'category': Exactly one of: ['Academic', 'Exam', 'Assignment', 'Placement', 'Fees', 'Event', 'Holiday', 'General'].\n"
                    "- 'priority': Exactly one of: ['Low', 'Medium', 'High']. 'High' is for strict/imminent deadlines, placement cutoffs, or disciplinary actions. 'Medium' is for normal course deadlines/events. 'Low' is for informational posts.\n"
                    "- 'deadline': Format as ISO date 'YYYY-MM-DD' if an explicit due date or deadline is stated; otherwise null.\n\n"
                    "Return ONLY raw JSON with these 4 keys."
                )

                user_prompt = f"Title: {title}\nAnnouncement Content:\n{content}"

                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    timeout=12.0,
                )

                raw_content = response.choices[0].message.content
                if raw_content:
                    data = json.loads(raw_content)
                    # Normalize category and priority casing
                    if "category" in data and isinstance(data["category"], str):
                        data["category"] = data["category"].capitalize()
                    if "priority" in data and isinstance(data["priority"], str):
                        data["priority"] = data["priority"].capitalize()

                    # Apply manual overrides if provided by admin
                    if manual_category:
                        data["category"] = manual_category
                    if manual_priority:
                        data["priority"] = manual_priority
                    if manual_deadline is not None:
                        data["deadline"] = manual_deadline

                    validated = AIAnalysisOutput(**data)
                    logger.info("Successfully analyzed notification via AI")
                    return validated

            except Exception as e:
                logger.warning(
                    f"AI analysis failed or timed out ({type(e).__name__}: {e}). Using heuristic fallback."
                )

        # Fallback to deterministic heuristics
        return self._heuristic_fallback(
            title=title,
            content=content,
            manual_category=manual_category,
            manual_priority=manual_priority,
            manual_deadline=manual_deadline,
        )

    def _heuristic_fallback(
        self,
        title: str,
        content: str,
        manual_category: Optional[str] = None,
        manual_priority: Optional[str] = None,
        manual_deadline: Optional[str] = None,
    ) -> AIAnalysisOutput:
        """
        Sensible, reliable fallback heuristics when AI is unavailable or fails.
        """
        combined = f"{title} {content}".lower()

        # 1. Category extraction
        if manual_category:
            category: NotificationCategory = manual_category  # type: ignore
        elif any(k in combined for k in ["exam", "midterm", "final exam", "hall ticket", "revaluation", "test schedule"]):
            category = "Exam"
        elif any(k in combined for k in ["placement", "campus drive", "recruitment", "interview", "resume", "internship", "package", "offer letter"]):
            category = "Placement"
        elif any(k in combined for k in ["fee", "tuition", "dues", "challan", "fine", "payment"]):
            category = "Fees"
        elif any(k in combined for k in ["assignment", "homework", "lab record", "submission", "project report"]):
            category = "Assignment"
        elif any(k in combined for k in ["holiday", "vacation", "declared holiday", "reopens on"]):
            category = "Holiday"
        elif any(k in combined for k in ["event", "fest", "symposium", "workshop", "webinar", "seminar", "cultural", "sports meet", "annual day"]):
            category = "Event"
        elif any(k in combined for k in ["syllabus", "lecture", "attendance", "curriculum", "faculty", "academic calendar"]):
            category = "Academic"
        else:
            category = "General"

        # 2. Priority determination
        if manual_priority:
            priority: NotificationPriority = manual_priority  # type: ignore
        elif any(k in combined for k in ["urgent", "immediately", "mandatory", "strictly", "penalty", "last date", "final call", "warning", "must"]):
            priority = "High"
        elif category in ["Exam", "Placement", "Fees"]:
            priority = "High"
        elif category in ["Assignment", "Event"]:
            priority = "Medium"
        elif category in ["Holiday", "General"]:
            priority = "Low"
        else:
            priority = "Medium"

        # 3. Deadline extraction
        deadline = manual_deadline
        if not deadline:
            # Match ISO format YYYY-MM-DD
            iso_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", content)
            if iso_match:
                deadline = iso_match.group(1)
            else:
                # Match DD/MM/YYYY or DD-MM-YYYY
                slash_match = re.search(r"\b(\d{2})[-/](\d{2})[-/](20\d{2})\b", content)
                if slash_match:
                    day, month, year = slash_match.groups()
                    deadline = f"{year}-{month}-{day}"

        # 4. Summary extraction
        # Take the first sentence or first 160 characters
        clean_text = " ".join(content.split())
        sentences = re.split(r"(?<=[.!?])\s+", clean_text)
        if sentences and len(sentences[0]) > 20:
            summary = sentences[0]
            if len(summary) > 200:
                summary = summary[:197].rsplit(" ", 1)[0] + "..."
        else:
            summary = clean_text[:180]
            if len(clean_text) > 180:
                summary = summary.rsplit(" ", 1)[0] + "..."

        return AIAnalysisOutput(
            summary=summary,
            category=category,
            priority=priority,
            deadline=deadline,
        )


ai_service = AIService()
