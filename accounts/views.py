from django.shortcuts import render
from django.contrib.auth import login,logout
from django.shortcuts import render,redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm

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
    return render(request, "accounts/dashboard.html",)