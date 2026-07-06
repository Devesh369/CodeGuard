from django.shortcuts import render , redirect ,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
import os
import json
import ast
from xml.sax.saxutils import escape

# for pdf
from reportlab.platypus import (SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Image
from django.conf import settings
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from django.core.exceptions import ValidationError
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.core.validators import validate_email
from smtplib import SMTPException
import threading


from .forms import UploadFileForm
from .models import UploadedFile , AnalysisReport
from .services.code_analyzer import (analyze_python_file)
from .services.security_analyzer import analyze_security

from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def parse_report_items(value):
    if not value:
        return []

    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError, ValueError):
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError, TypeError):
            return []

    if isinstance(parsed, list):
        return parsed

    if isinstance(parsed, dict):
        return [parsed]

    return []


def report_item_value(item, key, default="-"):
    if not isinstance(item, dict):
        return default

    value = item.get(key, default)

    if value in (None, ""):
        return default

    return value


def report_item_text(item, key, default="-"):
    return escape(str(report_item_value(item, key, default)))


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

    security = parse_report_items(report.security_report)


    # ------------------------
    # Pylint Report
    # ------------------------

    pylint = parse_report_items(report.pylint_json)


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
    
from io import BytesIO
@login_required
def download_pdf(request, report_id):


    report = get_object_or_404(
        AnalysisReport,
        id=report_id,
        uploaded_file__user=request.user,
    )

    pdf = generate_report_pdf(report)

    response = HttpResponse(
        pdf,
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="CodeGuard_Report_{report.id}.pdf"'
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


def delete_file(request, file_id):
    file = get_object_or_404(UploadedFile, id = file_id, user=request.user)
    if request.method == "POST":
        if file.file and os.path.isfile(file.file.path):
            os.remove(file.file.path)
            
        file.delete()
        messages.success(request,"File Deleted Successfully.")
        return redirect("my_files")
    return redirect("my_files")
    


def send_email_in_background(email_message):
    try:
        email_message.send()
        print("Email sent Successfully.")
    except Exception as e:
        print("Email Error : ",e)







    
@login_required
def send_report_email(request, report_id):
    report = get_object_or_404(
        AnalysisReport,
        id=report_id,
        uploaded_file__user=request.user,
    )

    if request.method != "POST":
        return redirect("report_detail", report.id)

    email = request.POST.get("email", "").strip()

    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, "Please enter a valid email address.")
        return redirect("report_detail", report.id)

    subject = "CodeGuard Analysis Report"
    plain_message = (
        "Hello,\n\n"
        "Your source code has been analyzed successfully.\n\n"
        f"File Name: {report.uploaded_file.file.name}\n"
        f"Quality Score: {report.pylint_score}/10\n"
        f"Security Issues: {report.security_issue_count}\n"
        f"Quality Status: {report.quality_status}\n\n"
        f"Recommendations:\n{report.recommendations}\n\n"
        "Thank you for using CodeGuard."
    )
    message = f"""
        <div style="font-family:Segoe UI,Arial,sans-serif;color:#1f2937;line-height:1.6">
            <h2 style="color:#1e3a8a;margin-bottom:8px">CodeGuard Analysis Report</h2>
            <p>Hello,</p>
            <p>Your source code has been analyzed successfully.</p>
            <table cellpadding="10" cellspacing="0" style="border-collapse:collapse;width:100%;max-width:620px">
                <tr>
                    <td style="background:#1e3a8a;color:#fff;font-weight:700">File Name</td>
                    <td style="background:#f8fafc">{escape(str(report.uploaded_file.file.name))}</td>
                </tr>
                <tr>
                    <td style="background:#1e3a8a;color:#fff;font-weight:700">Quality Score</td>
                    <td style="background:#f8fafc">{report.pylint_score}/10</td>
                </tr>
                <tr>
                    <td style="background:#1e3a8a;color:#fff;font-weight:700">Security Issues</td>
                    <td style="background:#f8fafc">{report.security_issue_count}</td>
                </tr>
                <tr>
                    <td style="background:#1e3a8a;color:#fff;font-weight:700">Quality Status</td>
                    <td style="background:#f8fafc">{escape(str(report.quality_status))}</td>
                </tr>
            </table>
            <h3 style="color:#1e3a8a;margin-top:22px">Recommendations</h3>
            <p>{escape(str(report.recommendations)).replace(chr(10), "<br>")}</p>
            <p>Thank you for using CodeGuard.</p>
        </div>
    """

    email_message = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            to=[email]
        )

    email_message.attach_alternative(message, "text/html")
    pdf = generate_report_pdf(report)

    email_message.attach(
        f"CodeGuard_Report_{report.id}.pdf",
        pdf,
        "application/pdf")
    
    thread = threading.Thread(target=send_email_in_background,args=(email_message,))
    thread.daemon = True

    thread.start()

    messages.success(request, "📧 Email request received. Your report is being sent in the background.")

    return redirect("report_detail",report.id)

def generate_report_pdf(report):

    buffer = BytesIO()
    

    doc = SimpleDocTemplate(
        buffer,
        leftMargin=30,
        rightMargin=30,
        topMargin=170,     # space for banner
        bottomMargin=110,
)

    styles = getSampleStyleSheet()

    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]
    pylint_issues = parse_report_items(report.pylint_json)
    security_issues = parse_report_items(report.security_report)

    story = []

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

    for issue in pylint_issues:
        quality_data.append([
            report_item_value(issue, "line"),
            report_item_value(issue, "code"),
            report_item_value(issue, "severity"),
            Paragraph(report_item_text(issue, "message"), normal_style),
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
    
    if security_issues:
            security_data = [["Line", "Severity", "CWE", "Description"]]
            for issue in security_issues:
                security_data.append([
                report_item_value(issue, "line"),
                report_item_value(issue, "severity"),
                report_item_value(issue, "cwe"),
                Paragraph(report_item_text(issue, "text"),normal_style)
            ])
            security_table = Table(
                security_data,
                colWidths=[50, 80, 80, 310],
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
# Header & Footer
# ==========================================================

    def draw_page(canvas, doc):

        page_width, page_height = doc.pagesize

        # ================= HEADER =================

        header_path = os.path.join(
            settings.BASE_DIR,
            "static",
            "images",
            "pdf_header.png"
        )

        if os.path.exists(header_path):

            banner_height = 160

            canvas.drawImage(
                header_path,
                x=0,
                y=page_height - banner_height,
                width=page_width,
                height=banner_height,
                preserveAspectRatio=False,
                mask="auto",
            )

        # ================= FOOTER =================

        footer_path = os.path.join(
            settings.BASE_DIR,
            "static",
            "images",
            "pdf_footer.png"
        )

        if os.path.exists(footer_path):

            footer_height = 90

            canvas.drawImage(
                footer_path,
                x=0,
                y=0,
                width=page_width,
                height=footer_height,
                preserveAspectRatio=False,
                mask="auto",
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
            onFirstPage=draw_page,
            onLaterPages=draw_page,
        )

    pdf = buffer.getvalue()
    buffer.close()

    return pdf