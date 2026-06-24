from django.shortcuts import render , redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import os

from .forms import UploadFileForm
from .models import UploadedFile , AnalysisReport
from .services.code_analyzer import (analyze_python_file)

@login_required
def upload_file(request):
    if request.method == "POST":
        
        form = UploadFileForm(request.POST, request.FILES)
        
        if form.is_valid():
            upload = form.save(commit = False)
            upload.user = request.user
            upload.save()
            filename = os.path.basename(upload.file.name)
            
            analysis = analyze_python_file(upload.file.path)
            AnalysisReport.objects.create(
                uploaded_file=upload,
                pylint_score=analysis["score"],
                pylint_report=analysis["report"],
                quality_status=analysis["quality"],
                issue_count=analysis["issues"],
                recommendations="\n".join(
                    analysis["recommendations"]
                )
            )
            messages.success(request, f"{filename} Uploaded successfully.")
                    
            return redirect ("my_files" ,)
       
        
    else:
        form = UploadFileForm()

    return render (request, "analyzer/upload.html", {"form":form , },)


@login_required
def my_files(request):
    files = UploadedFile.objects.filter(user=request.user)
    
    return render(request, "analyzer/my_files.html", {"files":files})



@login_required
def report_detail(request, report_id):
    report = AnalysisReport.objects.get(id=report_id)
    #score = float(report.pylint_score)

    
    
    return render(request, "analyzer/report.html",{"report":report, })