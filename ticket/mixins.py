from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class RoleBasedRedirectMixin:
    """
    Mixin to redirect users based on their role.
    """
    def get_redirect_url(self, user):
        if user.role == "admin":
            return "admin_dashboard"
        elif user.role == "staff":
            return "staff_dashboard"
        return "student_dashboard"
    
    
#------------------------------------ROLE REQUIRED MIXINS------------------------------------#

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'staff')

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'admin'

class StudentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'student')
    
class AdminOrStaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'staff') or self.request.user.role == 'admin'
