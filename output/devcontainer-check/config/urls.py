"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from library.views import (
    api_root,
    change_password,
    debug_email_test,
    health,
    home,
    login,
    logout,
    me,
    register,
)

urlpatterns = [
    path('', home),
    path('api/', api_root),
    path('admin/', admin.site.urls),
    path('api/health/', health),
    path('api/auth/register/', register),
    path('api/auth/login/', login),
    path('api/auth/logout/', logout),
    path('api/debug/email/test/', debug_email_test),
    path('api/users/me/', me),
    path('api/users/me/password/', change_password),
    path('api/library/', include('library.urls')),
]
