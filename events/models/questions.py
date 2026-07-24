from django.db import models
from core.models import UUIDPkField
from .event import Event

class CustomQuestion(UUIDPkField):
    class QuestionType(models.TextChoices):
        TEXT = "TEXT", "Text"
        DROPDOWN = "DROPDOWN", "Dropdown"
        CHECKBOX = "CHECKBOX", "Checkbox"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="custom_questions")
    question_text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=20, choices=QuestionType.choices, default=QuestionType.TEXT)
    options = models.JSONField(null=True, blank=True, help_text="List of options for DROPDOWN or CHECKBOX")
    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.question_text} ({self.event.title})"
