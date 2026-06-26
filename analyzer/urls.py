from django.urls import path
from .views import *


urlpatterns = [
    path("upload/",upload_file, name="upload_file"),
    path("files/",my_files,name="my_files"),
    path("report/<int:report_id>/",report_detail, name="report_detail"),
    path("report/<int:report_id>/pdf/", download_pdf, name="download_pdf"),
]