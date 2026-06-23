from django.shortcuts import render , redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import UploadFileForm
from .models import UploadedFile

@login_required
def upload_file(request):
    if request.method == "POST":
        
        form = UploadFileForm(request.POST, request.FILES)
        
        if form.is_valid():
            upload = form.save(commit = False)
            upload.user = request.user
            upload.save()
            messages.success(request, f"{upload.file.name} Uploaded successfully.")
            return redirect ("my_files")
       
        
    else:
        form = UploadFileForm()

    return render (request, "analyzer/upload.html", {"form":form},)


@login_required
def my_files(request):
    files = UploadedFile.objects.filter(user=request.user)
    
    return render(request, "analyzer/my_files.html", {"files":files})
