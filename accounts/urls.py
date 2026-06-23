from django.urls import path
from .views import dashboard , register_view , login_view , logout_view

urlpatterns = [
    path("",dashboard,name="dashboard"),
    path("register/",register_view,name="register"),
    path("login/",login_view,name="login"),
    path("logout/",logout_view,name="logout"),
]
