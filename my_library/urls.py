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
     StaffUpdateProfileView, home, LogInView, LogOutView, StaffTicketListView, StaffTicketDetailView,
    ManageTicketView, StaffProfileView, staff_dashboard, SignUpView,AdminTicketListView, AdminAccountsView,AdminAccountView,AdminAccountEditView,
     AdminAPITicketDetailsView,AdminAPIStaffByDepartmentView,AdminAPITicketAssignView,ForgetPasswordMailView,ForgetPasswordNewPasswordView
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
    path('forget-password/mail', ForgetPasswordMailView.as_view(), name='forget_password_mail'),
    path('forget-password/reset', ForgetPasswordNewPasswordView.as_view(), name='forget_password_reset_password'),
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
        path('announcements/', views.staff_announcements, name='staff_announcements'),
        path('tickets/', StaffTicketListView.as_view(), name='staff_ticket_list'),
        path('ticket/<int:ticket_id>/manage/', ManageTicketView.as_view(), name='manage_ticket'),
    ])),
     #------------------------------------admin URLS------------------------------------#

    path('control-panel/', include([
        path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
        path('tickets/', AdminTicketListView.as_view(), name='admin_ticket_list'),
        path('ticket/<int:ticket_id>/', StaffTicketDetailView.as_view(), name='admin_ticket_detail'),
        path('account/<int:account_id>/', AdminAccountEditView.as_view(), name='admin_edit_account'),
        path('account/', AdminAccountView.as_view(), name='admin_account'),
        path('accounts/', AdminAccountsView.as_view(), name='admin_accounts_list'),
        path('analytics/', views.analytics_dashboard, name='admin_analytics'),
        path('admin/export/tickets/', views.export_tickets_csv, name='export_tickets_csv'),
        path('admin/export/performance/', views.export_performance_csv, name='export_performance_csv'),
        path('announcements/', views.admin_announcements, name='admin_announcements'),
        path('announcements/create/', views.create_announcement, name='create_announcement'),
        path('announcements/delete/<int:announcement_id>/', views.delete_announcement, name='delete_announcement'),
        path('api/ticket_details', AdminAPITicketDetailsView.as_view(), name='api_ticket'),
        path('api/get_staff_by_department', AdminAPIStaffByDepartmentView.as_view(), name='api_get_staff_by_deparment'),
        path('api/ticket_assign', AdminAPITicketAssignView.as_view(), name='ticket_assign'),
        path('profile/', StaffProfileView.as_view(), name='admin_profile'),
        path('update_profile', StaffUpdateProfileView.as_view(), name='admin_update_profile'),
        path('control-panel/announcements/', views.admin_announcements, name='admin_announcements'),
        path('control-panel/announcements/create/', views.create_announcement, name='create_announcement'),
        path('control-panel/announcements/delete/<int:announcement_id>/', views.delete_announcement, name='delete_announcement'),
    ])),
    # General dashboard redirect
    path('verify-email/<uidb64>/<token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


