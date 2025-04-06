from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views import View
from django.urls import reverse
from django.conf import settings
from ticket import views
from django.conf.urls.static import static
from ticket.views import (
    StudentSettingsView, StaffUpdateProfileView, LogInView, LogOutView, 
    StaffTicketListView, StaffTicketDetailView, ManageTicketView, StaffProfileView,
    SignUpView,AdminTicketListView, AdminAccountsView,AdminAccountView,AdminAccountEditView,
    AdminAPITicketDetailsView,AdminAPIStaffByDepartmentView,AdminAPITicketAssignView,ForgetPasswordMailView,
    ForgetPasswordNewPasswordView,PasswordResetSentView, CreateTicketView,
    StudentTicketDetail, StaffDashboardView, AdminDashboardView, AdminAnalyticsDashboard,
    ExportTicketsView, ExportPerformanceView, AdminProfileView, AdminUpdateProfileView,
    AdminTicketDetailView, AdminAnnouncementsView, CreateAnnouncementView, DeleteAnnouncementView,
    CheckUsernameView, CheckEmailView, AboutView, FaqView, HomeView,
    DepartmentFormView,DepartmentListView
)

urlpatterns = [
    path('admin-panel/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('about/' , AboutView.as_view(), name='about'),
    path('faq/',FaqView.as_view(),name='faq'),
    
    #------------------------------------AUTHENTICATION URLS------------------------------------#
    path('login/', LogInView.as_view(), name='log_in'),
    path('logout/', LogOutView.as_view(), name='logout'),
    path('forget-password/mail', ForgetPasswordMailView.as_view(), name='forget_password_mail'),
    path('forget-password/reset/', ForgetPasswordNewPasswordView.as_view(), name='forget_password_reset_password'),
    path('forget-password/reset', ForgetPasswordNewPasswordView.as_view(), name='forget_password_reset_password'),
    path('sign_up/' , SignUpView.as_view() , name= 'sign_up'),
    path('forget-password/', views.ForgetPasswordMailView.as_view(), name='forget-password'),
    path('forget-password/sent/', PasswordResetSentView.as_view(), name='email-sent'),
    path('forget-password/reset/', views.PasswordResetView.as_view(), name='password-reset'),

    #-------------------------------AUTHENTICATION URLS--------------------------------#
    path('check_username/', CheckUsernameView.as_view(), name='check_username'),
    path('check_email/', CheckEmailView.as_view(), name='check_email'),
    
    #------------------------------------STUDENT URLS------------------------------------#
    path('student/', include([
        path('dashboard/', views.student_dashboard, name='student_dashboard'),
        path('settings/', StudentSettingsView.as_view(), name='student_settings'),
        path('tickets/', include([
            path('new/', CreateTicketView.as_view(), name='create_ticket'),
            path('<int:ticket_id>/', StudentTicketDetail.as_view(), name='ticket_detail'),
        ])),
    ])),
    #------------------------------------STAFF URLS------------------------------------#
    path('staff/', include([
        path('dashboard/', StaffDashboardView.as_view(), name='staff_dashboard'),
        path('profile/', StaffProfileView.as_view(), name='staff_profile'),
        path('tickets/', StaffTicketListView.as_view(), name='staff_ticket_list'),
        path('ticket/<int:ticket_id>/manage/', ManageTicketView.as_view(), name='manage_ticket'),
        path('update_profile', StaffUpdateProfileView.as_view(), name='staff_update_profile'),
        path('staff/ticket/<int:ticket_id>/', StaffTicketDetailView.as_view(), name='staff_ticket_detail'),
    ])),
    
    #------------------------------------ADMIN URLS------------------------------------#
    path('control-panel/', include([
        path('department/list', DepartmentListView.as_view(), name='admin_department_list'),
        path('department/', DepartmentFormView.as_view(), name='admin_department_create'),
        path('department/<int:department_id>/', DepartmentFormView.as_view(), name='admin_department_edit'),

        path('tickets/', AdminTicketListView.as_view(), name='admin_ticket_list'),
        # path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
        path('dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
        path('tickets/', AdminTicketListView.as_view(), name='admin_ticket_list'),
        path('ticket/<int:ticket_id>/', StaffTicketDetailView.as_view(), name='admin_ticket_detail'),
        path('account/<int:account_id>/', AdminAccountEditView.as_view(), name='admin_edit_account'),
        path('account/', AdminAccountView.as_view(), name='admin_account'),
        path('accounts/', AdminAccountsView.as_view(), name='admin_accounts_list'),
        path('analytics/', AdminAnalyticsDashboard.as_view(), name='admin_analytics'),
        path('admin/export/tickets/', ExportTicketsView.as_view(), name='export_tickets_csv'),
        path('admin/export/performance/', ExportPerformanceView.as_view(), name='export_performance_csv'),
        path('announcements/', AdminAnnouncementsView.as_view(), name='admin_announcements'),
        path('announcements/create/', CreateAnnouncementView.as_view(), name='create_announcement'),
        path('announcements/delete/<int:announcement_id>/', DeleteAnnouncementView.as_view(), name='delete_announcement'),
        path('api/ticket_details', AdminAPITicketDetailsView.as_view(), name='api_ticket'),
        path('api/get_staff_by_department', AdminAPIStaffByDepartmentView.as_view(), name='api_get_staff_by_deparment'),
        path('api/ticket_assign', AdminAPITicketAssignView.as_view(), name='ticket_assign'),
        path('profile/', StaffProfileView.as_view(), name='admin_profile'),
        path('update_profile', StaffUpdateProfileView.as_view(), name='admin_update_profile'),
        path('control-panel/announcements/', AdminAnnouncementsView.as_view(), name='admin_announcements'),
        path('control-panel/announcements/create/', CreateAnnouncementView.as_view(), name='create_announcement'),
        path('control-panel/announcements/delete/<int:announcement_id>/', DeleteAnnouncementView.as_view(), name='delete_announcement'),
        path('admin/profile/', AdminProfileView.as_view(), name='admin_profile'),
        path('admin/profile/edit/', AdminUpdateProfileView.as_view(), name='admin_update_profile'),
        path('control-panel/tickets/<int:ticket_id>/', AdminTicketDetailView.as_view(), name='admin_ticket_detail'),
        path('control-panel/account/<int:account_id>/', views.AdminAccountEditView.as_view(), name='admin_account_edit'),
        path('approve-staff/', views.AdminStaffApprovalListView.as_view(), name='admin_staff_approval_list'),
        path('approve-staff/<int:staff_profile_id>/', views.ApproveStaffUserView.as_view(), name='approve_staff_user'),

    ])),

    path('verify-email/<uidb64>/<token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


