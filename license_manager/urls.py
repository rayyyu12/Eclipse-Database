# File: license_manager/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # If you need API endpoints, uncomment the next line
    # path('api/', include('licenses.urls')),
]