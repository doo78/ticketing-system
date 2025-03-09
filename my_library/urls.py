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
     DashboardView, StaffUpdateProfileView, home, LogInView, LogOutView, StaffTicketListView, StaffTicketDetailView,
    ManageTicketView, StaffProfileView, staff_dashboard, SignUpView,AdminTicketListView, AdminAccountsView,AdminAccountView,AdminAccountEditView,
     AdminAPITicketDetailsView,AdminAPIStaffByDepartmentView,AdminAPITicketAssignView
)

from django.conf.urls.static import static


urlpatterns = [
    path('admin-panel/', admin.site.urls),
    path('', home, name='home'),
    path('about/' , views.about, name='about'),
    path('faq/',views.faq,name='faq'),
    
    #------------------------------------AUTHENTICATION URLS------------------------------------#
    path('login/', LogInView.as_view(), name='log_in'),
    path('logout/', LogOutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('sign_up/' , SignUpView.as_view() , name= 'sign_up'),

    #------------------------------------STAFF URLS------------------------------------#
    path('staff/dashboard/', staff_dashboard, name='staff_dashboard'),
    path('staff/tickets/', StaffTicketListView.as_view(), name='staff_ticket_list'),
    path('staff/ticket/<int:ticket_id>/', StaffTicketDetailView.as_view(), name='staff_ticket_detail'),
    path('staff/ticket/<int:ticket_id>/manage/', ManageTicketView.as_view(), name='manage_ticket'),
    path('staff/profile', StaffProfileView.as_view(), name='staff_profile'),
    path('staff/update_profile', StaffUpdateProfileView.as_view(), name='staff_update_profile'),
    #-------------------------------AUTHENTICATION URLS--------------------------------#

    path('check_username/', views.check_username, name='check_username'),
    path('check_email/', views.check_email, name='check_email'),
    
    #------------------------------------STUDENT URLS------------------------------------#
    path('student/', include([
        path('dashboard/', views.student_dashboard, name='student_dashboard'),
        path('settings/', views.student_settings, name='student_settings'),
        path('tickets/', include([
            path('', views.ticket_list, name='ticket_list'),
            path('new/', views.create_ticket, name='create_ticket'),
            path('<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
        ])),
    ])),
    #------------------------------------STAFF URLS------------------------------------#
    path('staff/', include([
        path('dashboard/', staff_dashboard, name='staff_dashboard'),
        path('profile/', StaffProfileView.as_view(), name='staff_profile'),
        path('tickets/', StaffTicketListView.as_view(), name='staff_ticket_list'),
        path('ticket/<int:ticket_id>/manage/', ManageTicketView.as_view(), name='manage_ticket'),
    ])),
     #------------------------------------STAFF URLS------------------------------------#

    path('control-panel/', include([
        path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
        path('tickets/', AdminTicketListView.as_view(), name='admin_ticket_list'),
        path('ticket/<int:ticket_id>/', StaffTicketDetailView.as_view(), name='admin_ticket_detail'),
        path('account/<int:account_id>/', AdminAccountEditView.as_view(), name='admin_edit_account'),
        path('account/', AdminAccountView.as_view(), name='admin_account'),
        path('accounts/', AdminAccountsView.as_view(), name='admin_accounts_list'),
        path('api/ticket_details', AdminAPITicketDetailsView.as_view(), name='api_ticket'),
        path('api/get_staff_by_department', AdminAPIStaffByDepartmentView.as_view(), name='api_get_staff_by_deparment'),
        path('api/ticket_assign', AdminAPITicketAssignView.as_view(), name='ticket_assign'),
        path('profile/', StaffProfileView.as_view(), name='admin_profile'),
        path('update_profile', StaffUpdateProfileView.as_view(), name='admin_update_profile'),

#
    ])),
    # General dashboard redirect
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

