from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from ticket.mixins import RoleBasedRedirectMixin
from .models import Ticket, Staff, CustomUser
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from ticket.forms import LogInForm, SignUpForm
from django.http import JsonResponse


def student_dashboard(request):
    # Dummy data for demonstration
    open_tickets = [
        {'id': 1, 'subject': 'Course Registration Issue', 'status': 'Open', 'created_at': '2024-02-05'},
        {'id': 2, 'subject': 'Library Access Problem', 'status': 'In Progress', 'created_at': '2024-02-04'},
    ]
    
    closed_tickets = [
        {'id': 3, 'subject': 'WiFi Connection Problem', 'status': 'Resolved', 'created_at': '2024-01-28'},
        {'id': 4, 'subject': 'Student ID Card Issue', 'status': 'Closed', 'created_at': '2024-01-20'},
    ]
    
    context = {
        'open_tickets': open_tickets,
        'closed_tickets': closed_tickets,
        'student_name': 'John Doe',  # Dummy student name
    }
    return render(request, 'ticket/dashboard.html', context)

def student_settings(request):
    # Dummy student data
    student_data = {
        'name': 'John Doe',
        'email': 'john.doe@university.edu',
        'student_id': '12345',
    }
    return render(request, 'ticket/settings.html', student_data)


def home(request):
    return render(request, 'home.html')


class LogInView(View, RoleBasedRedirectMixin):
    """
    Handles user login and redirection based on role.
    """
    def get(self, request):
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(self.get_redirect_url(user)) 
        messages.error(request, "Invalid username or password.")
        return render(request, 'login.html', {'form': form})  

    def render(self, request, next_page=''):
        """Render login template with blank log in form."""
        form = LogInForm()
        return render(request, 'login.html', {'form': form, 'next': next_page})


class LogOutView(View):
    """Log out the current user and redirect to login page."""

    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect(reverse("login"))  
    
class SignUpView(View, RoleBasedRedirectMixin):
    """
    Handles user registration using Django's Class-Based Views and Mixins.
    """
    def get(self, request):
        form = SignUpForm()
        return render(request, "sign_up.html", {"form": form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.role == 'staff':
                Staff.objects.create(
                    user=user,
                    department = '',
                    role = 'Staff Member'
                )
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('log_in')
        return render(request, "sign_up.html", {"form": form})   
    
class DashboardView(LoginRequiredMixin, View):
    """
    Display the appropriate dashboard based on the user's role.
    """

    def get(self, request, *args, **kwargs):
        role_dispatch = {
            'admin': self.render_admin_dashboard,
            'staff': self.render_staff_dashboard,
            'student': self.render_student_dashboard,
        }
        handler = role_dispatch.get(request.user.role, self.redirect_to_home)
        return handler(request)

    def render_admin_dashboard(self, request):
        """Render admin dashboard."""
        return render(request, 'admin_dashboard.html')

    def render_staff_dashboard(self, request):
        """Render staff dashboard."""
        return render(request, 'staff_dashboard.html')

    def render_student_dashboard(self, request):
        """Render student dashboard."""
        return render(request, 'student_dashboard.html')

    def redirect_to_home(self, request):
        """Redirect to home page if the role is undefined."""
        return redirect(reverse("home"))    
    
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'staff')



#@login_required
def staff_dashboard(request):
    '''
    if not hasattr(request.user, 'staff'):
        return redirect('home')
    

    
    context = {
        'assigned_tickets_count': Ticket.objects.filter(
            assigned_staff= request.user.staff
        ).exclude(status='closed').count(),
    }
    
    return render(request, 'staff/dashboard.html', context)
    '''
    return render(request, 'staff/dashboard.html')
    

#class ManageTicketView(LoginRequiredMixin, StaffRequiredMixin, View):
class ManageTicketView(View):
    def post(self, request, ticket_id):
        ticket = Ticket.objects.get(id=ticket_id)
        action = request.POST.get('action')

        if action == 'assign':
            ticket.assigned_staff = request.user.staff
            ticket.status = 'pending'
        elif action == 'close':
            ticket.status = 'closed'
            ticket.closed_by = request.user.staff
            ticket.date_closed = timezone.now()

        ticket.save()
        return redirect('staff_ticket_list')


#class StaffTicketListView(LoginRequiredMixin, StaffRequiredMixin, View):
class StaffTicketListView(View):
    
    def get(self, request):
        status = request.GET.get('status', 'all')

        # Base queryset
        tickets = Ticket.objects.all()

        # Filter by status if specified
        if status != 'all':
            tickets = tickets.filter(status=status)

        # Get counts for the filter buttons
        context = {
            'tickets': tickets,
            'status': status,
            'open_count': Ticket.objects.filter(status='open').count(),
            'pending_count': Ticket.objects.filter(status='pending').count(),
            'closed_count': Ticket.objects.filter(status='closed').count(),
        }
        return render(request, 'staff/staff_ticket_list.html', context)


#class StaffProfileView(LoginRequiredMixin, StaffRequiredMixin, View):
class StaffProfileView(View):
    
    def get(self, request):
        return render(request, 'staff/profile.html')


def check_username(request):
    username = request.GET.get('username', '')
    exists = CustomUser.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

def check_email(request):
    email = request.GET.get('email', '')
    exists = CustomUser.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})
