from django.shortcuts import render , redirect ,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
import os
import json
import ast

# for pdf
from reportlab.platypus import (SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Image
from django.conf import settings


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
    
@login_required
def download_pdf(request, report_id):

    report = get_object_or_404(
        AnalysisReport,
        id=report_id,
        uploaded_file__user=request.user,
    )

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        f'attachment; filename="CodeGuard_Report_{report.id}.pdf"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]

    story = []

    # ==========================================================
    # Banner
    # ==========================================================

    banner_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "images",
        "pdf-banner.png"
    )

    if os.path.exists(banner_path):

        banner = Image(
            banner_path,
            width=450,
            height=170
        )

        banner.hAlign = "CENTER"

        story.append(banner)

        story.append(Spacer(1, 20))

    else:

        title = Paragraph(
            "<b><font size='24'>CodeGuard</font></b>",
            styles["Title"]
        )

        story.append(title)

        subtitle = Paragraph(
            "<font size='14' color='gray'>AI Code Security Analysis Report</font>",
            styles["Heading2"]
        )

        story.append(subtitle)

        story.append(Spacer(1, 20))

    # ==========================================================
    # Summary Table
    # ==========================================================

    summary = [

        ["File", report.uploaded_file.file.name],

        ["Date", str(report.analyzed_at)],

        ["Quality Score", f"{report.pylint_score}/10"],

        ["Quality Status", report.quality_status],

        ["Code Issues", str(report.issue_count)],

        ["Security Issues", str(report.security_issue_count)],

    ]

    table = Table(
        summary,
        colWidths=[160, 320]
    )

    table.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#29408B")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (0, -1),
                colors.white
            ),

            (
                "BACKGROUND",
                (1, 0),
                (1, -1),
                colors.whitesmoke
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.grey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica-Bold"
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

        ])

    )

    story.append(table)

    story.append(Spacer(1, 0.4 * inch))

    # ==========================================================
    # Recommendations
    # ==========================================================

    story.append(

        Paragraph(
            "Recommendations",
            heading_style
        )

    )

    story.append(Spacer(1, 10))

    for rec in report.recommendations.split("\n"):

        if rec.strip():

            story.append(

                Paragraph(
                    f"• {rec}",
                    normal_style
                )

            )

            story.append(
                Spacer(1, 5)
            )

    story.append(
        Spacer(1, 20)
    )

    # ==========================================================
    # Footer
    # ==========================================================

    footer = Paragraph(

        "<b><i>Generated by CodeGuard</i></b>",

        styles["Heading3"]

    )

    story.append(footer)

    doc.build(story)

    return response