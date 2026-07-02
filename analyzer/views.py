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
from reportlab.platypus import Image
from django.conf import settings
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader


from .forms import UploadFileForm
from .models import UploadedFile , AnalysisReport
from .services.code_analyzer import (analyze_python_file)
from .services.security_analyzer import analyze_security

from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


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
    query = request.GET.get("q", "")
    files = UploadedFile.objects.filter(user=request.user)
    if query:
        files = files.filter(

        Q(file__icontains=query) |

        Q(analysisreport__quality_status__icontains=query)

        ).distinct()
    context = {
        "files": files,
        "query": query,
    }
        
    return render(
        request,
        "analyzer/my_files.html",
        context,
    )


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
        except (json.JSONDecodeError, TypeError, ValueError):
            try:
                security = ast.literal_eval(report.security_report)
            except Exception:
                security = []

    print(security)


    # ------------------------
    # Pylint Report
    # ------------------------

    pylint = []

    if report.pylint_json:
        try:
            pylint = json.loads(report.pylint_json)
        except (json.JSONDecodeError, TypeError, ValueError):
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


    # ------------------------
    # Context
    # ------------------------

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

    doc = SimpleDocTemplate(
            response,
            leftMargin=30,
            rightMargin=30,
            topMargin=20,
            bottomMargin=110
        )

    styles = getSampleStyleSheet()

    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]

    story = []

    # ==========================================================
    # Banner
    # ==========================================================

    header_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "images",
        "pdf_header.png"
        )


    if os.path.exists(header_path):

        header = Image(
            header_path,
            width=doc.width + doc.leftMargin + doc.rightMargin,
            height=3.0 * inch
        )

        header.hAlign = "CENTER"

        story.append(header)

        story.append(Spacer(1, 0.40 * inch))
        


    # ==========================================================
    # Summary Table
    # ==========================================================
    
    status = report.quality_status

    if status == "Excellent":
        status = "<font color='green'><b>Excellent</b></font>"

    elif status == "Good":
        status = "<font color='blue'><b>Good</b></font>"

    elif status == "Needs Improvement":
        status = "<font color='orange'><b>Needs Improvement</b></font>"

    else:
        status = "<font color='red'><b>Poor</b></font>"   
    summary = [

        ["File", os.path.basename(report.uploaded_file.file.name)],

        ["Date", report.analyzed_at.strftime("%d %B %Y %I:%M %p")],

        ["Quality Score", f"{report.pylint_score}/10"],

        ["Quality Status", Paragraph(status, normal_style)],

        ["Code Issues", str(report.issue_count)],

        ["Security Issues", str(report.security_issue_count)],

    ]

    table = Table(
        summary,
        colWidths=[180, 360]
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
    # PRINT DATA (pylint & bandint)
    # ==========================================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("Code Quality Issues", heading_style))
    story.append(Spacer(1, 10))
    
    quality_data = [
        ["Line", "Code", "Severity", "Description"]
]

    for issue in json.loads(report.pylint_json):
        quality_data.append([
            issue["line"],
            issue["code"],
            issue["severity"],
            issue["message"],
        ])
        
    quality_table = Table(
    quality_data,
    colWidths=[50,60,90,320],
    repeatRows=1
    )
    quality_table.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#29408B")),
    ("TEXTCOLOR",(0,0),(-1,0),colors.white),
    ("GRID",(0,0),(-1,-1),0.5,colors.grey),
    ("BACKGROUND",(0,1),(-1,-1),colors.whitesmoke),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
    ("BOTTOMPADDING",(0,0),(-1,0),8),
    ("VALIGN",(0,0),(-1,-1),"TOP"),
    
    ]))
    
    story.append(quality_table)
    
    
    story.append(Spacer(1,20))
    story.append(Paragraph("Security Issues", heading_style))
    story.append(Spacer(1,10))
    
    security_data = [
    ["Line", "Severity", "Confidence", "CWE", "Description"]]
    
    security_data.append([
    issue.get("line", "-"),
    issue.get("severity", "-"),
    issue.get("confidence", "-"),
    issue.get("cwe", "-"),
    Paragraph(issue.get("text", "-"), normal_style)
])

    try:
        security = json.loads(report.security_report)
        print(json.dumps(security, indent=4))
        
        
    except:
        security = []
        print(json.dumps(security, indent=4))
    
    if security:
            security_data = [["Line", "Severity", "CWE", "Description"]]
            for issue in security:
                security_data.append([
                issue.get("line", "-"),
                issue.get("severity", "-"),
                issue.get("cwe", "-"),
                Paragraph(issue.get("text", "-"),normal_style)
            ])
                security_table = Table(
                    security_data,
                    colWidths=[40, 60, 70, 50, 320],
                    repeatRows=1
                )
            
            security_table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#B91C1C")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey),
            ("BACKGROUND",(0,1),(-1,-1),colors.whitesmoke),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("BOTTOMPADDING",(0,0),(-1,0),8),
            ]))
            
            story.append(security_table)
    else:
            story.append(
        Paragraph(
            "<font color='green'><b>✓ No security vulnerabilities detected.</b></font>",
            normal_style
        )
    )
            
        
        

    # ==========================================================
    # Recommendations
    # ==========================================================

    story.append(Spacer(1, 20))
    story.append(Paragraph("Recommendations", heading_style))
    story.append(Spacer(1, 10))

    for rec in report.recommendations.split("\n"):

        rec = rec.strip()

        if rec:

            story.append(
                Paragraph(
                f"<font color='#16A34A'><b>✔</b></font> {rec}",
                normal_style
            )
        )
    # ==========================================================
    # Footer
    # ==========================================================
    def draw_footer(canvas, doc):

        footer_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "images",
        "pdf_footer.png"
        )

        if os.path.exists(footer_path):

            footer = ImageReader(footer_path)

            page_width, page_height = doc.pagesize
            
            
            
            canvas.drawImage(
                footer,
                x=0,
                y=10,
                width = doc.width + doc.leftMargin + doc.rightMargin,
                height=1.85 * inch,
                preserveAspectRatio=False,
                mask="auto"
            )

            canvas.saveState()

            canvas.setFont("Helvetica", 9)

            canvas.drawRightString(
                page_width - 30,
                15,
                f"Page {doc.page}"
            )

            canvas.restoreState()

    doc.build(
    story,
    onFirstPage=draw_footer,
    onLaterPages=draw_footer
    )

    return response



@login_required
def search_files(request):

    q=request.GET.get("q","")

    files=UploadedFile.objects.filter(

        user=request.user,

        file__icontains=q

    )[:10]

    data=[]

    for file in files:

        report=AnalysisReport.objects.filter(

            uploaded_file=file

        ).first()

        data.append({

            "name":file.file.name.replace("uploads/",""),

            "report_id":report.id if report else None

        })

    return JsonResponse(data,safe=False)