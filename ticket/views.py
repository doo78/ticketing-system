from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse
from ticket.mixins import RoleBasedRedirectMixin
from ticket.forms import LogInForm, SignUpForm, StaffUpdateProfileForm
from .models import Ticket, Staff, CustomUser, Student
from .forms import TicketForm
from django.views.generic.edit import UpdateView

#------------------------------------STUDENT SECTION------------------------------------#
@login_required
def create_ticket(request):
    if not hasattr(request.user, 'student'):
        raise PermissionDenied("Only students can create tickets")

    if request.method == 'POST':
        form = TicketForm(request.POST, student=request.user.student)
        if form.is_valid():
            ticket = form.save()
            messages.success(request,
                           'Your ticket has been submitted successfully. Ticket number: #{}'.format(ticket.id))
            return redirect('student_dashboard')  # Changed to match your URL name
    else:
        form = TicketForm(student=request.user.student)

    return render(request, 'student/create_ticket.html', {
        'form': form
    })
@login_required
def student_settings(request):
    if not hasattr(request.user, 'student'):
        return redirect('home')

    student_data = {
        'name': request.user.get_full_name(),
        'email': request.user.email,
        'preferred_name': request.user.preferred_name,
        'department': request.user.student.department,
        'program': request.user.student.program,
        'year_of_study': request.user.student.year_of_study
    }
    return render(request, 'student/settings.html', student_data)


@login_required
def ticket_list(request):
    if not hasattr(request.user, 'student'):
        return redirect('home')

    tickets = Ticket.objects.filter(student=request.user.student)
    return render(request, 'student/ticket_list.html', {'tickets': tickets})

#------------------------------------STAFF SECTION------------------------------------#

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'staff')

def home(request):
    return render(request, 'home.html')

@login_required
def staff_dashboard(request):
    if not hasattr(request.user, 'staff'):
        return redirect('home')

    context = {
        'assigned_tickets_count': Ticket.objects.filter(
            assigned_staff=request.user.staff
        ).exclude(status='closed').count(),
        'department': request.user.staff.department or "Not Assigned"
    }
    return render(request, 'staff/dashboard.html', context)


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
        return redirect(reverse("log_in"))
    
class SignUpView(View):
    """
    Handles user registration using Django's Class-Based Views.
    """
    def get(self, request):
        form = SignUpForm()
        return render(request, "sign_up.html", {"form": form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.role == 'staff':
                Staff.objects.create(user=user, department='', role='Staff Member')
            elif user.role == 'student':
                Student.objects.create(
                    user=user,
                    department=form.cleaned_data.get('department', ''),
                    program=form.cleaned_data.get('program', 'Undeclared'),
                    year_of_study=form.cleaned_data.get('year_of_study', 1)
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
        return render(request, 'staff/dashboard.html')

    def render_student_dashboard(self, request):
        """Render student dashboard."""
        return render(request, 'student/dashboard.html')

    def redirect_to_home(self, request):
        """Redirect to home page if the role is undefined."""
        return redirect(reverse("home"))    
    
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'staff')

class StudentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'student')

#@login_required
def staff_dashboard(request):
    return render(request, 'staff/dashboard.html')

@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'student'):
        return redirect('home')

    open_tickets = Ticket.objects.filter(
        student=request.user.student
    ).exclude(status='closed')

    closed_tickets = Ticket.objects.filter(
        student=request.user.student,
        status='closed'
    )
    context = {
        'open_tickets': open_tickets,
        'closed_tickets': closed_tickets,
        'student_name': request.user.preferred_name or request.user.first_name,
    }
    return render(request, 'student/dashboard.html', context)

class ManageTicketView(LoginRequiredMixin, StaffRequiredMixin, View):
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


class StaffTicketListView(LoginRequiredMixin, StaffRequiredMixin, View):
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


class StaffProfileView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request):
        return render(request, 'staff/profile.html')
    
class StaffUpdateProfileView(UpdateView):
    
    model = CustomUser
    template_name = "staff/update_profile.html"
    form_class = StaffUpdateProfileForm
    
    def get_object(self):
        """Return the object (user) to be updated."""
        return self.request.user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        
        messages.add_message(self.request, messages.SUCCESS, "Profile updated")
        return reverse("staff_profile")  


def check_username(request):
    username = request.GET.get('username', '')
    exists = CustomUser.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

def check_email(request):
    email = request.GET.get('email', '')
    exists = CustomUser.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})
