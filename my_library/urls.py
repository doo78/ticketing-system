from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views import View
from django.urls import reverse
from django.conf import settings
from ticket import views
from ticket.views import (
    DashboardView, home, LogInView, LogOutView, StaffTicketListView, 
    ManageTicketView, StaffProfileView, staff_dashboard, SignUpView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    
    #------------------------------------AUTHENTICATION URLS------------------------------------#
    path('login/', LogInView.as_view(), name='log_in'),
    path('logout/', LogOutView.as_view(), name='logout'),
    path('sign_up/', SignUpView.as_view(), name='sign_up'),
    path('check_username/', views.check_username, name='check_username'),
    path('check_email/', views.check_email, name='check_email'),
    
    #------------------------------------STUDENT URLS------------------------------------#
    path('student/', include([
        path('dashboard/', views.student_dashboard, name='student_dashboard'),
        path('settings/', views.student_settings, name='student_settings'),
        path('tickets/', include([
            path('', views.ticket_list, name='ticket_list'),
            path('new/', views.create_ticket, name='create_ticket'),
        ])),
    ])),
    #------------------------------------STAFF URLS------------------------------------#
    path('staff/', include([
        path('dashboard/', staff_dashboard, name='staff_dashboard'),
        path('profile/', StaffProfileView.as_view(), name='staff_profile'),
        path('tickets/', StaffTicketListView.as_view(), name='staff_ticket_list'),
        path('ticket/<int:ticket_id>/manage/', ManageTicketView.as_view(), name='manage_ticket'),
    ])),
    
    # General dashboard redirect
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]