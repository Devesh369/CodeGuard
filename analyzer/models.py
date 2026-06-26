from django.db import models
from accounts.models import User


class UploadedFile(models.Model):
    STATUS_CHOICES = [
        ("Pending","Pending"),
        ("Analyzed", "Analyzed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="uploads/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    uploaded_At = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return self.file.name
    
    
    
class AnalysisReport(models.Model):
    uploaded_file = models.OneToOneField(UploadedFile, on_delete=models.CASCADE)
    pylint_score = models.FloatField(max_length=10)
    pylint_report = models.TextField()
    analyzed_at = models.DateTimeField(auto_now_add=True)
    issue_count = models.IntegerField(default=0)
    quality_status = models.CharField(max_length=30,default="Unknown")
    recommendations = models.TextField(blank=True)
    pylint_json = models.TextField(blank=True)
    
    security_score = models.IntegerField(default=100)
    security_issue_count = models.IntegerField(default=0)
    security_report = models.TextField(blank=True)
    
    def __str__(self):
        return (f"Report -" f"{self.uploaded_file.file.name}")