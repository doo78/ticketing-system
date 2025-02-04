"""
URL configuration for my_library project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views import View
from django.urls import reverse
from django.conf import settings
from ticket import views
from ticket.views import (
    home,
    StaffTicketListView,
    ManageTicketView,
    staff_dashboard
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('' , home , name='home'),
    #------------------------------------STUDENT URLS------------------------------------#
    path('student/tickets/new/', views.create_ticket, name='create_ticket'),
    path('student/tickets/', views.ticket_list, name='ticket_list'),
    #------------------------------------STAFF URLS------------------------------------#
    path('staff/dashboard/', staff_dashboard, name='staff_dashboard'),
    path('staff/tickets/', StaffTicketListView.as_view(), name='staff_ticket_list'),
    path('staff/ticket/<int:ticket_id>/manage/', ManageTicketView.as_view(), name='manage_ticket'),

    #------------------------------------AUTHENTICATION URLS------------------------------------#
]
