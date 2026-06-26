from django.shortcuts import render
from django.contrib.auth import login,logout
from django.shortcuts import render,redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from django.db.models import Avg, Sum , FloatField
from analyzer.models import UploadedFile, AnalysisReport
from django.db.models.functions import Cast


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            login(request , user)
            return redirect ("dashboard")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html",{"form":form},)





def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request,user)
            return redirect("dashboard")
    else:
        form = AuthenticationForm()
        
    return render(request, "accounts/login.html",{"form":form},) 
 
 
 
 
 
         
def logout_view(request):
    logout(request)
    return redirect("login")





@login_required
def dashboard(request):
    files = UploadedFile.objects.filter(
        user=request.user
    )

    reports = AnalysisReport.objects.filter(
        uploaded_file__user=request.user
    )

    avg = reports.annotate(
    score_float=Cast("pylint_score", FloatField())
    ).aggregate(
        Avg("score_float")
    )

    excellent = reports.filter(
        quality_status="Excellent"
    ).count()

    good = reports.filter(
        quality_status="Good"
    ).count()

    improve = reports.filter(
        quality_status="Needs Improvement"
    ).count()

    poor = reports.filter(
        quality_status="Poor"
    ).count()

    security = reports.aggregate(
        Sum("security_issue_count")
    )

    recent = reports.order_by(
        "-analyzed_at"
    )[:5]

    context = {

        "total_files": files.count(),

        "analyzed_files": reports.count(),

        "average_score": round(avg["score_float__avg"] or 0,2),

        "security_count":
            security["security_issue_count__sum"] or 0,

        "excellent": excellent,
        "good": good,
        "improve": improve,
        "poor": poor,

        "recent": recent,
    }

    return render(
        request,
        "accounts/dashboard.html",
        context
    )