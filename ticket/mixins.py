from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin

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