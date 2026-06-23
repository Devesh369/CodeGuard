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
    