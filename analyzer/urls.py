from django.urls import path
from .views import *


urlpatterns = [
    path("upload/",upload_file, name="upload_file"),
    path("files/",my_files,name="my_files"),
    path("report/<int:report_id>/",report_detail, name="report_detail"),
    path("report/<int:report_id>/pdf/", download_pdf, name="download_pdf"),
    path("search_files/",search_files, name="search_files"),
    path("delete_project/<int:project_id>/", delete_project , name="delete_project"),
    path("report/<int:report_id>/send-email/", send_report_email , name="send_report_email"),
    
    
]
