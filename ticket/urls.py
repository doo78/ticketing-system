from django.urls import path
from . import views

app_name = 'ticket'

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='dashboard'),
    path('settings/', views.student_settings, name='settings'),
] 