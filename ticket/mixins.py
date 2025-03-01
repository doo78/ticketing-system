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
    


class AdminRoleRequiredMixin(LoginRequiredMixin):
    """
    Only allows users with role='admin' to access the view.
    Assumes `request.user.role` is defined.
    """
    def dispatch(self, request, *args, **kwargs):
        # Ensure the user is authenticated first
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check custom role
        if request.user.role != 'admin':
            raise PermissionDenied("You do not have permission to access this resource.")
        
        return super().dispatch(request, *args, **kwargs)    