from django.db import models
from accounts.models import User

class Project(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Analyzing", "Analyzing"),
        ("Completed", "Completed"),
        ("Failed", "Failed"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=25,)
    overall_score = models.FloatField(default=0)
    total_issues = models.IntegerField(default=0)
    total_security_issues = models.IntegerField(default=0)
    project_summary = models.TextField(blank=True)
    top_improvements = models.JSONField(default=list)
    code_smells = models.JSONField(default=list)
    technical_debt = models.JSONField(default=list)
    overall_suggestions = models.JSONField(default=list)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="Pending")
    total_files = models.IntegerField(default=0)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name



class UploadedFile(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Analyzed", "Analyzed"),
    ]

    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        related_name="files",
        null=True,
        blank=True,
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    file = models.FileField(upload_to="uploads/")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    # New fields (temporarily optional)
    original_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    relative_path = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    file_size = models.BigIntegerField(default=0)

    language = models.CharField(
        max_length=20,
        default="Python",
    )

    def __str__(self):
        return self.file.name    
    
class AnalysisReport(models.Model):
    uploaded_file = models.OneToOneField(UploadedFile,on_delete=models.CASCADE,related_name="analysis",)
    pylint_score = models.FloatField(max_length=10)
    pylint_report = models.TextField()
    analyzed_at = models.DateTimeField(auto_now_add=True)
    issue_count = models.IntegerField(default=0)
    quality_status = models.CharField(max_length=30,default="Unknown")
    recommendations = models.JSONField(blank=True)
    pylint_json = models.TextField(blank=True)
    
    security_level = models.CharField(max_length=10, default="Safe")
    security_issue_count = models.IntegerField(default=0)
    security_report = models.TextField(blank=True)
    
    ai_score = models.FloatField(default=0)
    ai_summary = models.TextField(blank=True)
    ai_strengths = models.JSONField(default=list)
    ai_weaknesses = models.JSONField(default=list)
    ai_suggestions = models.JSONField(default=list)
    ai_changes = models.JSONField(default=list)
    ai_fixed_code = models.TextField(blank=True)
    ai_fix_explanation = models.TextField(blank=True)
    maintainability_score = models.FloatField(default=0)
    readability_score = models.FloatField(default=0)
    ai_security = models.CharField(max_length=30, blank=True)
    ai_confidence = models.FloatField(default=0)
    analysis_duration = models.FloatField(default=0)
        
    
    
    def __str__(self):
        return (f"Report -" f"{self.uploaded_file.file.name}")