from django.shortcuts import render , redirect ,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import os
import json
import ast

from .forms import UploadFileForm
from .models import UploadedFile , AnalysisReport
from .services.code_analyzer import (analyze_python_file)
from .services.security_analyzer import analyze_security


@login_required
def upload_file(request):

    if request.method == "POST":

        form = UploadFileForm(request.POST, request.FILES)

        print("FILES:", request.FILES)

        if form.is_valid():

            print("FORM VALID")

            try:

                upload = form.save(commit=False)
                upload.user = request.user
                upload.save()

                print("File Saved")

                analysis = analyze_python_file(upload.file.path)
                print("Pylint Done")

                security = analyze_security(upload.file.path)
                print("Bandit Done")

                AnalysisReport.objects.create(
                    uploaded_file=upload,
                    pylint_score=analysis["score"],
                    pylint_report=analysis["report"],
                    pylint_json=json.dumps(
                        analysis["pylint_issues"],
                        indent=4
                    ),
                    quality_status=analysis["quality"],
                    issue_count=analysis["issues"],
                    recommendations="\n".join(
                        analysis["recommendations"]
                    ),
                    security_issue_count=security["issue_count"],
                    security_report=json.dumps(
                        security["issues"],
                        indent=4
                    ),
                )

                print("Report Saved")

                upload.status = "Analyzed"
                upload.save()

                filename = os.path.basename(upload.file.name)

                messages.success(
                    request,
                    f"{filename} uploaded successfully."
                )

                print("Redirecting")

                return redirect("my_files")

            except Exception as e:

                print("ERROR OCCURRED")
                print(e)

        else:

            print(form.errors)

    else:

        form = UploadFileForm()

    return render(
        request,
        "analyzer/upload.html",
        {"form": form}
    )




@login_required
def my_files(request):
    files = UploadedFile.objects.filter(user=request.user)
    
    return render(request, "analyzer/my_files.html", {"files":files})


@login_required
def report_detail(request, report_id):

    report = get_object_or_404(
        AnalysisReport,
        id=report_id
    )

    # ------------------------
    # Security Report
    # ------------------------

    security = []

    if report.security_report:

        try:
            security = json.loads(report.security_report)

        except json.JSONDecodeError:

            try:
                security = ast.literal_eval(report.security_report)

            except Exception:
                security = []

    # ------------------------
    # Pylint Report
    # ------------------------

    pylint = []

    if report.pylint_json:

        try:
            pylint = json.loads(report.pylint_json)

        except json.JSONDecodeError:

            try:
                pylint = ast.literal_eval(report.pylint_json)

            except Exception:
                pylint = []
                
    print(pylint)

    # ------------------------
    # Recommendations
    # ------------------------

    recommendations = []

    if report.recommendations:
        recommendations = report.recommendations.split("\n")

    context = {
        "report": report,
        "security": security,
        "pylint": pylint,
        "recommendations": recommendations,
    }

    return render(
        request,
        "analyzer/report.html",
        context,
    )