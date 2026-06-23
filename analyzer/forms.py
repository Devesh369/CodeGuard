from django import forms
from .models import UploadedFile

class UploadFileForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ["file"]
        
        
    def clean_file(self):
        file = self.cleaned_data["file"]
        if not file.name.endswith(".py"):
            raise forms.ValidationError("Only PYTHON FILES are allowed ‼️")
        return file
        
    
