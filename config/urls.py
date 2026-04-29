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
    catalog_resolve,
    catalog_search,
    change_password,
    frontend,
    health,
    login,
    logout,
    me,
    register,
)

urlpatterns = [
    # Muestra la interfaz web principal de la biblioteca.
    path('', frontend),
    # Abre el panel de administracion de Django.
    path('admin/', admin.site.urls),
    # Comprueba que la API esta activa.
    path('api/health/', health),
    # Busca juegos por texto en el catalogo externo.
    path('api/catalog/search/', catalog_search),
    # Resuelve varios IDs externos a datos minimos para el frontend.
    path('api/catalog/resolve/', catalog_resolve),
    # Registra un usuario nuevo.
    path('api/auth/register/', register),
    # Inicia sesion con un usuario existente.
    path('api/auth/login/', login),
    # Cierra la sesion actual, exista o no un usuario autenticado.
    path('api/auth/logout/', logout),
    # Cambia la contrasena del usuario autenticado.
    path('api/users/me/password/', change_password),
    # Devuelve o elimina los datos del usuario autenticado.
    path('api/users/me/', me),
    # Agrupa las rutas de gestion de entradas de la biblioteca.
    path('api/library/', include('library.urls')),
]
