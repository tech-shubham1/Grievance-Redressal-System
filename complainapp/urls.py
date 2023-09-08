from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.handleLogin, name="handleLogin"),
    path('signup', views.handleSignup, name="handleSignup"),
    path('logout', views.handleLogout, name="handleLogout"),
    path('respondcomplain', views.respondComplain, name="respondComplain"),
    path('createcomplain', views.createComplain, name="createComplain"),
    path('allcomplain', views.allcomplain, name = "allcomplain"),
    path('postlike', views.postlike, name='postlike'),
    path('reopencomplain', views.reopenComplain, name='reopenComplain'),
    path('escalatecomplain', views.escalateComplain, name='escalateComplain'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
