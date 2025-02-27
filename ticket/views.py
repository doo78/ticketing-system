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
from .models import Ticket, Staff, Student, CustomUser, Message
from .forms import TicketForm
from django.views.generic.edit import UpdateView


from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Avg
from datetime import timedelta
from .models import Ticket
from django.db import models 
from django.utils.timezone import now
from django.db.models import F, Avg

from django.db.models import ExpressionWrapper, DurationField

from django.db.models import F, ExpressionWrapper, DurationField, Case, When, Value
from django.db.models.functions import Cast
from django.db.models import FloatField

# #Gen AI imports
import boto3
from botocore.config import Config
import json
from django.views.decorators.http import require_POST

#------------------------------------STUDENT SECTION------------------------------------#
@login_required
def create_ticket(request):
    if not hasattr(request.user, 'student'):
        raise PermissionDenied("Only students can create tickets")

    if request.method == 'POST':
        form = TicketForm(request.POST, student=request.user.student)
        if form.is_valid():
            ticket = form.save()

            if ticket.department:
                matching_staff = Staff.objects.filter(department=ticket.department)
                if matching_staff.exists():
                    assigned_staff = None
                    min_active_tickets = float('inf')

                    for staff in matching_staff:
                        active_ticket_count = Ticket.objects.filter(
                            assigned_staff=staff,
                        ).exclude(
                            status = 'closed'
                        ).count()

                        if active_ticket_count < min_active_tickets:
                            min_active_tickets = active_ticket_count
                            assigned_staff = staff

                    if assigned_staff:
                        ticket.assigned_staff = assigned_staff
                        ticket.status = 'pending'
                        ticket.save()

                        messages.success(
                            request,
                            f'Your ticket #{ticket.id} has been successfully submitted and assigned to a staff member from {ticket.get_department_display()}'
                        )
                        return redirect('student_dashboard')

            messages.success(
                request,
                f'Your ticket #{ticket.id} has been submitted successfully. We will review it shortly.'
            )
            return redirect('student_dashboard')
    else:
        form = TicketForm(student=request.user.student)

    return render(request, 'student/create_ticket.html', {
        'form': form,
        'title': 'Submit New Query'
    })

@login_required
def student_settings(request):
    if not hasattr(request.user, 'student'):
        return redirect('home')

    # Get the user's last login time
    last_login = request.user.last_login
    if last_login:
        from django.utils import timezone
        from django.utils.timezone import localtime
        now = timezone.now()
        if now.date() == last_login.date():
            last_login_display = f"Today at {localtime(last_login).strftime('%I:%M %p')}"
        else:
            last_login_display = localtime(last_login).strftime('%B %d, %Y %I:%M %p')
    else:
        last_login_display = "Never"

    student_data = {
        'name': request.user.get_full_name(),
        'email': request.user.email,
        'preferred_name': request.user.preferred_name,
        'department': request.user.student.department,
        'program': request.user.student.program,
        'year_of_study': request.user.student.year_of_study,
        # Account status information
        'account_type': request.user.get_role_display(),
        'status': 'Active',  # You can add logic for different statuses if needed
        'member_since': localtime(request.user.date_joined).strftime('%B %d, %Y'),
        'last_login': last_login_display,
    }
    return render(request, 'student/settings.html', student_data)


@login_required
def ticket_list(request):
    if not hasattr(request.user, 'student'):
        return redirect('home')

    tickets = Ticket.objects.filter(student=request.user.student)
    return render(request, 'student/ticket_list.html', {'tickets': tickets})

@login_required
def ticket_detail(request, ticket_id):
    if not hasattr(request.user, 'student'):
        return redirect('home')
    
    ticket = get_object_or_404(Ticket, id=ticket_id, student=request.user.student)
    
    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content:
            if ticket.status == 'closed':
                messages.error(request, 'Cannot add messages to a closed ticket.')
                return render(request, 'student/ticket_detail.html', {
                    'ticket': ticket,
                    'ticket_messages': ticket.messages.all().order_by('created_at')
                })
            Message.objects.create(
                ticket=ticket,
                author=request.user,
                content=message_content
            )
            messages.success(request, 'Message sent successfully.')
            return redirect('ticket_detail', ticket_id=ticket_id)
    
    context = {
        'ticket': ticket,
        'ticket_messages': ticket.messages.all().order_by('created_at')
    }
    return render(request, 'student/ticket_detail.html', context)

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

    staff_department = request.user.staff.department

    # Count tickets assigned to this staff member
    assigned_tickets_count = Ticket.objects.filter(
        assigned_staff=request.user.staff
    ).exclude(status='closed').count()

    # Count tickets for their department (not necessarily assigned to them)
    department_tickets_count = 0
    if staff_department:
        department_tickets_count = Ticket.objects.filter(
            department=staff_department
        ).exclude(status='closed').count()

    # Count unassigned tickets in their department
    unassigned_dept_tickets = 0
    if staff_department:
        unassigned_dept_tickets = Ticket.objects.filter(
            department=staff_department,
            assigned_staff=None,
            status='open'
        ).count()

    context = {
        'assigned_tickets_count': assigned_tickets_count,
        'department_tickets_count': department_tickets_count,
        'unassigned_dept_tickets': unassigned_dept_tickets,
        'department': request.user.staff.get_department_display() if staff_department else "Not Assigned"
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
            redirect_url = self.get_redirect_url(user)
            # Check if it's a direct URL or a URL name
            if redirect_url.startswith('/'):
                return redirect(redirect_url)
            return redirect(redirect_url)
        messages.error(request, "Invalid username or password.")
        return render(request, 'login.html', {'form': form})  

    def render(self, request, next_page=''):
        """Render login template with blank log in form."""
        form = LogInForm()
        return render(request, 'login.html', {'form': form, 'next': next_page})


class LogOutView(View):
    """Log out the current user and redirect to login page."""

    def get(self, request):
        # Clear all existing messages
        storage = messages.get_messages(request)
        storage.used = True
        
        # Perform logout
        logout(request)
        
        # Add only the logout success message
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
            'admin': self.render_staff_dashboard,  # Admin users see staff dashboard
            'staff': self.render_staff_dashboard,
            'student': self.render_student_dashboard,
        }
        handler = role_dispatch.get(request.user.role, self.redirect_to_home)
        return handler(request)

    def render_staff_dashboard(self, request):
        """Render staff dashboard."""
        
        context = {
            'assigned_tickets_count': Ticket.objects.filter(
                assigned_staff=request.user.staff if hasattr(request.user, 'staff') else None
            ).exclude(status='closed').count(),
            'department': request.user.staff.department if hasattr(request.user, 'staff') else "Admin"
        }
        return render(request, 'staff/dashboard.html', context)

    def render_student_dashboard(self, request):
        student = request.user.student
        name = request.user.preferred_name if request.user.preferred_name else request.user.first_name

        # Get tickets by status
        open_tickets = Ticket.objects.filter(student=student, status='open').order_by('-date_submitted')
        pending_tickets = Ticket.objects.filter(student=student, status='pending').order_by('-date_submitted')
        closed_tickets = Ticket.objects.filter(student=student, status='closed').order_by('-date_submitted')

        # For display purposes, we show both open and pending tickets in the active section
        active_tickets = list(open_tickets) + list(pending_tickets)
        active_tickets.sort(key=lambda x: x.date_submitted, reverse=True)

        context = {
            'student_name': name,
            'open_tickets': open_tickets,  # Only open tickets
            'pending_tickets': pending_tickets,  # Only pending tickets
            'closed_tickets': closed_tickets,  # Only closed tickets
            'active_tickets': active_tickets,  # Combined open and pending tickets for display
        }
        return render(request, 'student/dashboard.html', context)

    def redirect_to_home(self, request):
        """Redirect to home page if the role is undefined."""
        return redirect(reverse("home"))    
    
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'staff')

class StudentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'student')

@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'student'):
        return redirect('home')

    # Get tickets by status
    open_tickets = Ticket.objects.filter(student=request.user.student, status='open').order_by('-date_submitted')
    pending_tickets = Ticket.objects.filter(student=request.user.student, status='pending').order_by('-date_submitted')
    closed_tickets = Ticket.objects.filter(student=request.user.student, status='closed').order_by('-date_submitted')

    # For display purposes, we show both open and pending tickets in the active section
    active_tickets = list(open_tickets) + list(pending_tickets)
    active_tickets.sort(key=lambda x: x.date_submitted, reverse=True)

    context = {
        'student_name': request.user.preferred_name or request.user.first_name,
        'open_tickets': open_tickets,  # Only open tickets
        'pending_tickets': pending_tickets,  # Only pending tickets
        'closed_tickets': closed_tickets,  # Only closed tickets
        'active_tickets': active_tickets,  # Combined open and pending tickets for display
    }
    return render(request, 'student/dashboard.html', context)

class ManageTicketView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request, ticket_id):
        ticket = Ticket.objects.get(id=ticket_id)
        action = request.POST.get('action')

        # Get the current filter parameters to preserve them after redirect
        status_filter = request.POST.get('status_filter', 'all')
        department_filter = request.POST.get('department_filter', 'all')

        if action == 'assign':
            ticket.assigned_staff = request.user.staff
            ticket.status = 'pending'
        elif action == 'close':
            ticket.status = 'closed'
            ticket.closed_by = request.user.staff
            ticket.date_closed = timezone.now()

        ticket.save()

        # Redirect back to the same filtered view
        redirect_url = reverse('staff_ticket_list')
        params = []

        if status_filter != 'all':
            params.append(f'status={status_filter}')

        if department_filter != 'all':
            params.append(f'department_filter={department_filter}')

        if params:
            redirect_url += '?' + '&'.join(params)

        return redirect(redirect_url)


class StaffTicketListView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request):
        status = request.GET.get('status', 'all')
        department_filter = request.GET.get('department_filter', 'all')

        tickets = Ticket.objects.all()

        # Filter by status if specified
        if department_filter == 'mine':
            staff_department = request.user.staff.department
            if staff_department:
                tickets = tickets.filter(department=staff_department)

        if status != 'all':
            tickets = tickets.filter(status=status)

        # Get counts for the filter buttons
        context = {
            'tickets': tickets,
            'status': status,
            'department_filter': department_filter,
            'open_count': Ticket.objects.filter(status='open').count(),
            'pending_count': Ticket.objects.filter(status='pending').count(),
            'closed_count': Ticket.objects.filter(status='closed').count(),
            'my_department_count': Ticket.objects.filter(
                department= request.user.staff.department
            ).count() if request.user.staff.department else 0,
        }
        return render(request, 'staff/staff_ticket_list.html', context)

class StaffTicketDetailView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Display ticket details for staff members"""
    def get(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)
        context = {
            'ticket': ticket,
            'ticket_messages': ticket.messages.all().order_by('created_at')
        }
        return render(request, 'staff/ticket_detail.html', context)

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)
        
        # Check if this is a JSON request (AI generation)
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                action = data.get('action')
                current_text = data.get('current_text', '')
                # Prepare data for Lambda
                lambda_client = boto3.client(
                    'lambda',
                    region_name=settings.AWS_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    config=Config(
                        retries=dict(
                            max_attempts=2
                        )
                    )
                )
                
                lambda_payload = {
                    "ticket_id": ticket.id,
                    "department": ticket.department,
                    "subject": ticket.subject,
                    "description": ticket.description,
                    "student_name": ticket.student.user.get_full_name(),
                    "student_program": ticket.student.program,
                    "student_year": ticket.student.year_of_study,
                    "staff_name": request.user.get_full_name(),
                    "staff_department": request.user.staff.department,
                    "action": action,
                    "current_text": current_text,
                    "messages": [
                        {
                            "author": msg.author.get_full_name(),
                            "content": msg.content
                        } for msg in ticket.messages.all()
                    ]
                }

                try:
                    response = lambda_client.invoke(
                        FunctionName=settings.LAMBDA_FUNCTION_NAME,
                        InvocationType='RequestResponse',
                        Payload=json.dumps(lambda_payload)
                    )
                    
                    if response['StatusCode'] != 200:
                        raise Exception(f"Lambda returned status code {response['StatusCode']}")
                    
                    response_payload = json.loads(response['Payload'].read())
                    
                    if 'errorMessage' in response_payload:
                        raise Exception(response_payload['errorMessage'])
                    
                    if response_payload.get('statusCode') == 200:
                        body = json.loads(response_payload['body'])
                        return JsonResponse({
                            'success': True,
                            'response': body['response']
                        })
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': response_payload.get('body', 'Unknown error')
                        })

                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': f"Failed to generate AI response: {str(e)}"
                    })

            except json.JSONDecodeError as e:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON in request'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': 'An unexpected error occurred'
                })
            
        # Handle regular form submission (adding messages)
        message_content = request.POST.get('message')
        if message_content:
            if ticket.status == 'closed':
                messages.error(request, 'Cannot add messages to a closed ticket.')
            else:
                Message.objects.create(
                    ticket=ticket,
                    author=request.user,
                    content=message_content
                )
                messages.success(request, 'Message sent successfully.')
        
        return redirect('staff_ticket_detail', ticket_id=ticket_id)

class StaffProfileView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    Loads relevant data and template for staff profile
    """
    
    def get(self, request):
        staff_member = request.user.staff  

        assigned_tickets = Ticket.objects.filter(assigned_staff=staff_member)
        
        open_tickets = assigned_tickets.filter(status="open").count()
        pending_tickets = assigned_tickets.filter(status="pending").count()
        closed_tickets = assigned_tickets.filter(status="closed").count()
        
        total_tickets = open_tickets + pending_tickets + closed_tickets

        if total_tickets > 0:
            open_percentage = (open_tickets / total_tickets) * 100
            pending_percentage = (pending_tickets / total_tickets) * 100
            closed_percentage = (closed_tickets / total_tickets) * 100
        else:
            open_percentage = 0 
            pending_percentage = 0 
            closed_percentage = 0

        if closed_tickets == 0:
            avg_close_time_days_display = "N/A"
        else:
            avg_close_time = Ticket.objects.filter(
                status="closed", 
                date_closed__isnull=False
            ).aggregate(
                avg_duration=Avg(ExpressionWrapper(Case(When(date_closed__gte=F("date_submitted"),  
                            then=F("date_closed") - F("date_submitted")),
                            default=Value(0),
                            output_field=DurationField()  
                        ),
                        output_field=DurationField()  
                    )
                )
            )

            avg_duration = avg_close_time["avg_duration"]
            if avg_duration:
                avg_close_time_days = avg_duration.days + avg_duration.seconds / (3600 * 24)
                avg_close_time_days = round(avg_close_time_days, 2)
                avg_close_time_days_display = f"{avg_close_time_days} days"
            else:
                avg_close_time_days_display = "N/A"

        context = {
            "open_tickets": open_tickets,
            "pending_tickets": pending_tickets,
            "closed_tickets": closed_tickets,
            "total_tickets": total_tickets,
            "open_percentage": open_percentage,
            "pending_percentage": pending_percentage,
            "closed_percentage": closed_percentage,
            "avg_close_time_days": avg_close_time_days_display
        }
        
        return render(request, 'staff/profile.html', context)

class StaffUpdateProfileView(UpdateView):
    """
    Loads the page and form to update the staff profile
    """
    
    model = CustomUser
    template_name = "staff/update_profile.html"
    form_class = StaffUpdateProfileForm
    
    def get_object(self):
        """Return the object (user) to be updated."""
        return self.request.user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        
        return reverse("staff_profile")  


def check_username(request):
    username = request.GET.get('username', '')
    exists = CustomUser.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

def check_email(request):
    email = request.GET.get('email', '')
    exists = CustomUser.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})
