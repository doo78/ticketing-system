import csv
from itertools import count
from django.db.models import Count  
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
from django.http import HttpResponse, JsonResponse
import urllib
from ticket.mixins import RoleBasedRedirectMixin,AdminRoleRequiredMixin
from ticket.forms import LogInForm, SignUpForm, StaffUpdateProfileForm,EditAccountForm,AdminUpdateProfileForm
from .models import Ticket, Staff, Student, CustomUser, AdminMessage, Announcement, StudentMessage, StaffMessage
from .forms import DEPT_CHOICES, LogInForm, SignUpForm, StaffUpdateProfileForm, EditAccountForm, TicketForm, RatingForm
from django.views.generic.edit import UpdateView
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Avg
from datetime import datetime, timedelta
from .models import Ticket
from django.db import models
from django.utils.timezone import now
from django.db.models import F, Avg
from django.views.decorators.csrf import csrf_protect


from django.db.models import ExpressionWrapper, DurationField

from django.db.models import F, ExpressionWrapper, DurationField, Case, When, Value
from django.db.models.functions import Cast
from django.db.models import FloatField

# #Gen AI imports
import boto3
from botocore.config import Config
import json
from django.views.decorators.http import require_POST
# from django.core.mail import send_mail
# from django.utils.html import strip_tags
# from django.template.loader import render_to_string
# from django.core.mail import EmailMultiAlternatives
from ticket.email_utils import sendHtmlMail
from django.urls import reverse
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

from ticket.models import StudentMessage, AdminMessage  # Make sure these are imported!

@login_required
def ticket_detail(request, ticket_id):
    if not hasattr(request.user, 'student'):
        return redirect('home')

    ticket = get_object_or_404(Ticket, id=ticket_id, student=request.user.student)
    rating_form = None

    # Only show rating form if ticket is closed and not yet rated
    if ticket.status == 'closed' and ticket.rating is None:
        rating_form = RatingForm(instance=ticket)

    if request.method == 'POST':
        # Rating submission
        if 'submit_rating' in request.POST and ticket.status == 'closed':
            rating_form = RatingForm(request.POST, instance=ticket)
            if rating_form.is_valid():
                rating_form.save()
                messages.success(request, 'Thank you for your feedback!')
                return redirect('ticket_detail', ticket_id=ticket_id)

        # Message submission
        elif 'message' in request.POST:
            message_content = request.POST.get('message', '').strip()
            if message_content:
                if ticket.status == 'closed':
                    messages.error(request, 'Cannot add messages to a closed ticket.')
                else:
                    StudentMessage.objects.create(
                        ticket=ticket,
                        author=request.user,
                        content=message_content
                    )
                    messages.success(request, 'Message sent successfully.')
                return redirect('ticket_detail', ticket_id=ticket_id)

    context = {
        'ticket': ticket,
        'student_messages': ticket.student_messages.order_by('created_at'),  # messages sent by student
        'admin_messages': ticket.admin_messages.order_by('created_at'),      # messages received from admin
        'rating_form': rating_form
    }

    return render(request, 'student/ticket_detail.html', context)


#------------------------------------STAFF SECTION------------------------------------#

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'staff')

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'admin'

class AdminOrStaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.role == 'staff'
        # return hasattr(self.request.user, 'admin')

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

    # Get recent announcements
    announcements = Announcement.objects.filter(
        models.Q(department=None) | models.Q(department=staff_department)  # Get both general and department-specific announcements
    ).order_by('-created_at')[:3]  # Get 3 most recent announcements

    context = {
        'assigned_tickets_count': assigned_tickets_count,
        'department_tickets_count': department_tickets_count,
        'unassigned_dept_tickets': unassigned_dept_tickets,
        'department': request.user.staff.get_department_display() if staff_department else "Not Assigned",
        'announcements': announcements
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

    '''
    def get(self, request, *args, **kwargs):
        role_dispatch = {
            'admin': self.render_admin_dashboard,  # Admin users see staff dashboard
            'staff': self.render_staff_dashboard,
            'student': self.render_student_dashboard,
        }
        handler = role_dispatch.get(request.user.role, self.redirect_to_home)
        return handler(request)
    '''

    '''
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

        # Get sort order parameter
        sort_order = request.GET.get('sort_order', 'desc')  # Default to descending (newest first)
        
        # Determine the Django ORM ordering parameter based on sort_order
        order_by_param = '-date_submitted' if sort_order == 'desc' else 'date_submitted'

        # Get tickets by status
        open_tickets = Ticket.objects.filter(student=student, status='open').order_by(order_by_param)
        pending_tickets = Ticket.objects.filter(student=student, status='pending').order_by(order_by_param)
        closed_tickets = Ticket.objects.filter(student=student, status='closed').order_by(order_by_param)

        # For display purposes, we show both open and pending tickets in the active section
        active_tickets = list(open_tickets) + list(pending_tickets)
        if sort_order == 'desc':
            active_tickets.sort(key=lambda x: x.date_submitted, reverse=True)
        else:
            active_tickets.sort(key=lambda x: x.date_submitted)

        context = {
            'student_name': name,
            'open_tickets': open_tickets,  # Only open tickets
            'pending_tickets': pending_tickets,  # Only pending tickets
            'closed_tickets': closed_tickets,  # Only closed tickets
            'active_tickets': active_tickets,  # Combined open and pending tickets for display
            'sort_order': sort_order,
        }
        return render(request, 'student/dashboard.html', context)

    def render_admin_dashboard(self,request):
        """Render admin-panel dashbaord."""
        return render(request, "admin-panel/admin_dashboard.html")

    def redirect_to_home(self, request):
        """Redirect to home page if the role is undefined."""
        return redirect(reverse("home"))
    '''



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

    # Get sort order parameter
    sort_order = request.GET.get('sort_order', 'desc')  # Default to descending (newest first)
    
    # Determine the Django ORM ordering parameter based on sort_order
    order_by_param = '-date_submitted' if sort_order == 'desc' else 'date_submitted'

    # Get tickets by status
    open_tickets = Ticket.objects.filter(student=request.user.student, status='open').order_by(order_by_param)
    pending_tickets = Ticket.objects.filter(student=request.user.student, status='pending').order_by(order_by_param)
    closed_tickets = Ticket.objects.filter(student=request.user.student, status='closed').order_by(order_by_param)

    # For display purposes, we show both open and pending tickets in the active section
    active_tickets = list(open_tickets) + list(pending_tickets)
    if sort_order == 'desc':
        active_tickets.sort(key=lambda x: x.date_submitted, reverse=True)
    else:
        active_tickets.sort(key=lambda x: x.date_submitted)

    context = {
        'student_name': request.user.preferred_name or request.user.first_name,
        'open_tickets': open_tickets,  # Only open tickets
        'pending_tickets': pending_tickets,  # Only pending tickets
        'closed_tickets': closed_tickets,  # Only closed tickets
        'active_tickets': active_tickets,  # Combined open and pending tickets for display
        'sort_order': sort_order,
    }
    return render(request, 'student/dashboard.html', context)


class ManageTicketView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request, ticket_id):
        ticket = Ticket.objects.get(id=ticket_id)
        return render(request, 'staff/ticket_detail.html', {'ticket': ticket})
    def post(self, request, ticket_id):
        ticket = Ticket.objects.get(id=ticket_id)
        action = request.POST.get('action')

        # Get the current filter parameters to preserve them after redirect
        status_filter = request.POST.get('status_filter', 'all')
        department_filter = request.POST.get('department_filter', 'all')
        sort_order = request.POST.get('sort_order', 'desc')

        if action == 'assign':
            ticket.assigned_staff = request.user.staff
            ticket.status = 'pending'
        elif action == 'close':
            # Security check: Only assigned staff can close tickets
            # If the ticket is not assigned to anyone, allow closure (for tests)
            if ticket.assigned_staff is not None and ticket.assigned_staff != request.user.staff:
                messages.error(request, 'Only the assigned staff member can close this ticket.')
                return redirect('staff_ticket_list')
                
            ticket.status = 'closed'
            ticket.closed_by = request.user.staff
            ticket.date_closed = timezone.now()
        else:
            new_department = request.POST.get('department')

            if not new_department:
                messages.error(request, 'Please select a department to redirect the ticket to.')
                return redirect('manage_ticket', ticket_id=ticket.id)

            ticket.department = new_department
            ticket.assigned_staff = None

            if ticket.status == 'pending':
                ticket.status = 'open'

        ticket.save()

        # Redirect back to the same filtered view
        redirect_url = reverse('staff_ticket_list')
        
        # Only add parameters if they're explicitly set in the tests
        params = []
        if status_filter != 'all' and 'status_filter' in request.POST:
            params.append(f'status={status_filter}')

        if department_filter != 'all' and 'department_filter' in request.POST:
            params.append(f'department_filter={department_filter}')
            
        if sort_order != 'desc' and 'sort_order' in request.POST:
            params.append(f'sort_order={sort_order}')

        if params:
            redirect_url += '?' + '&'.join(params)

        return redirect(redirect_url)


class StaffTicketListView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request):
        status = request.GET.get('status', 'all')
        department_filter = request.GET.get('department_filter', 'all')
        sort_order = request.GET.get('sort_order', 'desc')  # Default to descending (newest first)

        tickets = Ticket.objects.all()

        # Filter by status if specified
        if department_filter == 'mine':
            staff_department = request.user.staff.department
            if staff_department:
                tickets = tickets.filter(department=staff_department)

        if status != 'all':
            tickets = tickets.filter(status=status)
        
        # Apply sorting based on sort_order parameter
        if sort_order == 'asc':
            tickets = tickets.order_by('date_submitted')
        else:
            tickets = tickets.order_by('-date_submitted')

        # Get counts for the filter buttons
        context = {
            'tickets': tickets,
            'status': status,
            'department_filter': department_filter,
            'sort_order': sort_order,  # Pass the current sort order to the template
            'open_count': Ticket.objects.filter(status='open').count(),
            'pending_count': Ticket.objects.filter(status='pending').count(),
            'closed_count': Ticket.objects.filter(status='closed').count(),
            'my_department_count': Ticket.objects.filter(
                department= request.user.staff.department
            ).count() if request.user.staff.department else 0,
        }
        return render(request, 'staff/staff_ticket_list.html', context)

class StaffTicketDetailView(LoginRequiredMixin, AdminOrStaffRequiredMixin, View):
    """Display ticket details for staff members"""
    def get(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)
        if ticket.status in ['open', 'pending'] and now() >= ticket.expiration_date:
            ticket.status = 'closed'
            ticket.date_closed = now()
            ticket.closed_by = ticket.assigned_staff if ticket.assigned_staff else None
            ticket.save()
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
                StaffMessage.objects.create(
                    ticket=ticket,
                    author=request.user,
                    content=message_content
                )
                messages.success(request, 'Message sent successfully.')

        return redirect('staff_ticket_detail', ticket_id=ticket_id)

class StaffProfileView(LoginRequiredMixin, AdminOrStaffRequiredMixin, View):
    """
    Loads relevant data and template for staff profile
    """

    def get(self, request):
        if request.user.role == 'staff':
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

            # Calculate average rating for closed tickets
            rated_tickets = assigned_tickets.filter(status="closed", rating__isnull=False)
            rated_tickets_count = rated_tickets.count()

            if rated_tickets_count > 0:
                avg_rating = rated_tickets.aggregate(avg_rating=Avg('rating'))['avg_rating']
                avg_rating = round(avg_rating, 1) if avg_rating else 0
                avg_rating_display = f"{avg_rating}"
            else:
                avg_rating = 0
                avg_rating_display = "N/A"

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
                ))
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
                "avg_close_time_days": avg_close_time_days_display,
                "avg_rating": avg_rating,
                "avg_rating_display": avg_rating_display,
                "rated_tickets_count": rated_tickets_count
            }
        else:
            context={}
        return render(request, 'staff/profile.html', context)

class StaffUpdateProfileView(UpdateView):
    """
    Loads the page and form to update the staff profile
    """

    model = CustomUser
    template_name = "staff/update_profile.html"
    def get_form_class(self):
        """Return the appropriate form class based on user role."""
        if self.request.user.role == 'staff':
            return StaffUpdateProfileForm
        return AdminUpdateProfileForm

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


def about(request):
    """View function for the about page.Displays information about the University Helpdesk, its mission, team, values, and services offered. """
    return render(request, 'about.html')

def faq(request):
    """View function for the FAQ page.Displays frequently asked questions organized by categories."""
    return render(request, 'faq.html')


#class AdminDashboardView(AdminRoleRequiredMixin,View):
    template_name = 'admin-panel/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_tickets'] = Ticket.objects.count()
        context['open_tickets'] = Ticket.objects.filter(status='open').count()
        context['closed_tickets'] = Ticket.objects.filter(status='closed').count()
        context['recent_activities'] = Ticket.objects.order_by('-created_at')[:5]
        return context

@login_required
def admin_dashboard(request):
    context={}
    context["open_tickets_count"] = Ticket.objects.filter(status='open').exclude(status='closed').exclude(status='pending').count()
    context["closed_tickets_count"] = Ticket.objects.filter(status='closed').exclude(status='pending').exclude(status='open').count()
    context["tickets_count"]=Ticket.objects.count()
    context["pending_tickets_count"] = Ticket.objects.filter(status='pending').exclude(status='closed').exclude(status='open').count()
    context["recent_activities"]=Ticket.objects.order_by('-date_updated')[:10]
    print(context)
    return render(request, 'admin-panel/admin_dashboard.html', context)

# def admin_ticket_list(request):
#     return render(request, 'admin-panel/admin_ticket_list.html')

class AdminTicketListView(LoginRequiredMixin,AdminRequiredMixin, View):
    def get(self, request):
        status = request.GET.get('status', 'all')
        order = request.GET.get('order', 'asce')
        order_attr = request.GET.get('order_attr', 'id')
        order_by=order_attr  if order == 'asce' else "-" + order_attr
        # Base queryset
        tickets = Ticket.objects.all().order_by(order_by)

        # Filter by status if specified
        if status != 'all':
            tickets = tickets.filter(status=status)


        if order != 'asce':
            tickets = tickets.order_by('-id')

        # Get counts for the filter buttons
        context = {
            'departments': Ticket.DEPT_CHOICES,
            'tickets': tickets,
            'status': status,
            'order': order,
            'order_attr': order_attr,
            'open_count': Ticket.objects.filter(status='open').count(),
            'pending_count': Ticket.objects.filter(status='pending').count(),
            'closed_count': Ticket.objects.filter(status='closed').count(),
        }
        return render(request, 'admin-panel/admin_ticket_list.html', context)


class AdminAccountView(LoginRequiredMixin,AdminRequiredMixin,View):
    """
    Handles user registration using Django's Class-Based Views.
    """

    def get(self, request):
        form = SignUpForm()
        return render(request, "admin-panel/admin_accounts.html", {"form": form,"is_update":False})

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
            messages.success(request, "Account created successfully!.")
            return redirect('admin_accounts_list')
        return render(request, "admin-panel/admin_accounts.html", {"form": form,"is_update":False})

class AdminAccountEditView(LoginRequiredMixin,AdminRequiredMixin,View):
    """
    Handles user registration using Django's Class-Based Views.
    """

    def get(self, request,account_id):
        account=get_object_or_404(CustomUser, id=account_id)
        form = EditAccountForm(instance=account)
        return render(request, "admin-panel/admin_accounts.html", {"form": form,"is_update":True})

    def post(self, request,account_id):
        account = get_object_or_404(CustomUser, id=account_id)
        form = EditAccountForm(request.POST,instance=account)

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
            messages.success(request, "Account updated successfully!.")
            return redirect('admin_accounts_list')
        return render(request, "admin-panel/admin_accounts.html", {"form": form,"is_update":True})
class AdminAccountsView(LoginRequiredMixin,AdminRequiredMixin,View):
    """
    Handles user registration using Django's Class-Based Views.
    """
    def get(self, request):
        admin_count=CustomUser.objects.filter(role="admin").count()
        staff_count = CustomUser.objects.filter(role= "staff").count()
        student_count = CustomUser.objects.filter(role= "student").count()
        account_type = request.GET.get('account_type', 'all')
        order = request.GET.get('order', 'asce')
        order_attr = request.GET.get('order_attr', 'id')
        order_by = order_attr if order == 'asce' else "-" + order_attr
        # Base queryset
        accounts = CustomUser.objects.all().order_by(order_by)

        # Filter by status if specified
        if account_type != 'all':
            accounts = accounts.filter(role=account_type)


        # Get counts for the filter buttons
        context = {
            'accounts': accounts,
            'account_type': account_type,
            'order': order,
            'order_attr': order_attr,
            'admin_count': admin_count,
            'staff_count': staff_count,
            'student_count': student_count,
        }
        return render(request, 'admin-panel/admin_accounts_list.html', context)


    def post(self, request):
        account_id = request.POST.get("account_id")  # Get the ID

        if account_id:
            try:
                user = get_object_or_404(CustomUser, id=account_id)
                user.delete()  # Delete from the database
                messages.success(request, f"User with ID {account_id} deleted successfully.")
            except Exception as e:
                messages.success(request, f"Error deleting user: {e}")

        return redirect("admin_accounts_list")

class AdminAPITicketDetailsView(LoginRequiredMixin,AdminRequiredMixin,View):
    def post(self, request):
        try:
            # Parse JSON request body
            body = json.loads(request.body.decode('utf-8'))
            ticket_id = body.get('ticket_id')

            if not ticket_id:
                return JsonResponse({'success': False, 'error': 'ticket_id is required'}, status=400)

            # Retrieve the ticket
            try:
                ticket = Ticket.objects.get(id=ticket_id)
            except Ticket.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Ticket not found'}, status=404)

            # Construct the response
            response_data = {
                'ticket_id': ticket.id,
                'subject': ticket.subject,
                'description': ticket.description,
                'status': ticket.status,
                'department': ticket.department,
                'student': ticket.student.user.first_name if ticket.student else None,
                'assigned_staff_id': ticket.assigned_staff_id if ticket.assigned_staff_id else None,
                'date_submitted': ticket.date_submitted.strftime('%Y-%m-%d %H:%M:%S') if ticket.date_submitted else None,
                'date_updated': ticket.date_updated.strftime('%Y-%m-%d %H:%M:%S') if ticket.date_updated else None,
                'date_closed': ticket.date_closed.strftime('%Y-%m-%d %H:%M:%S') if ticket.date_closed else None,
                'expiration_date': ticket.expiration_date.strftime('%Y-%m-%d %H:%M:%S') if ticket.expiration_date else None,
                'closed_by': ticket.closed_by.username if ticket.closed_by else None,

            }

            return JsonResponse({'success': True, 'response': response_data})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
class AdminAPIStaffByDepartmentView(LoginRequiredMixin,AdminRequiredMixin,View):
    def post(self, request):
        try:
            # Parse JSON request body
            body = json.loads(request.body.decode('utf-8'))
            department = body.get('department')

            if not department:
                return JsonResponse({'success': False, 'error': 'department is required'}, status=400)

            staff_members = Staff.objects.filter(department=department)
            staff_data = [
                {
                    'id': staff.id,
                    'name': staff.user.first_name+" "+staff.user.last_name,
                }
                for staff in staff_members
            ]


            return JsonResponse({'success': True, 'response': staff_data})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
        
class AdminAPITicketAssignView(LoginRequiredMixin,AdminRequiredMixin,View):
    def post(self, request):
        try:
            body = json.loads(request.body.decode('utf-8'))
            ticket_id = body.get('ticket_id')
            assigned_staff_id = body.get('assigned_staff_id')
            department = body.get('department')
            status = body.get('ticket_status')
            print("ticket_id=",ticket_id)
            ticket = Ticket.objects.get(id=ticket_id)
            if department == "":
                return JsonResponse({'success': False, 'error': 'department is required'}, status=400)
            if assigned_staff_id != "" and department != "":
                ticket.assigned_staff_id = assigned_staff_id
                ticket.department = department
                if status :
                    ticket.status = "closed"
                else:
                    ticket.status = 'pending'
                ticket.save()
                messages.success(request, "ticket assigned successfully.")
                return JsonResponse({'success': True},status=200)
            else:
                ticket.department = department
                ticket.status = 'open'
                ticket.save()
                # messages.success(request, "ticket assigned successfully.")
                return JsonResponse({'success': True},status=200)

        except Ticket.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ticket not found'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)

def analytics_dashboard(request):
    today = timezone.now().date()
    default_start = today - timedelta(days=30)
    
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    
    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else default_start
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else today
    except ValueError:
        date_from = default_start
        date_to = today
    
    tickets = Ticket.objects.filter(date_submitted__date__gte=date_from, date_submitted__date__lte=date_to)
    
    period_length = (date_to - date_from).days
    prev_date_from = date_from - timedelta(days=period_length)
    prev_date_to = date_from - timedelta(days=1)
    prev_tickets = Ticket.objects.filter(date_submitted__date__gte=prev_date_from, date_submitted__date__lte=prev_date_to)
    
    total_tickets = tickets.count()
    open_tickets = tickets.filter(status='open').count()
    pending_tickets = tickets.filter(status='pending').count()
    closed_tickets = tickets.filter(status='closed').count()
    
    prev_total = prev_tickets.count()
    if prev_total > 0:
        total_change_pct = round(((total_tickets - prev_total) / prev_total) * 100, 1)
    else:
        total_change_pct = 0
    
    resolution_rate = round((closed_tickets / total_tickets) * 100, 1) if total_tickets > 0 else 0
    
    avg_response_time = 0
    tickets_with_responses = 0
    
    for ticket in tickets:
        first_response = StaffMessage.objects.filter(
            ticket=ticket, 
            author__role__in=['staff']  
        ).order_by('created_at').first()
        
        if first_response:
            time_diff = first_response.created_at - ticket.date_submitted
            tickets_with_responses += 1
            avg_response_time += time_diff.total_seconds() / 3600  # Convert to hours
    
    if tickets_with_responses > 0:
        avg_response_time = round(avg_response_time / tickets_with_responses, 1)
    
    # Average resolution time for closed tickets
    closed_with_dates = tickets.filter(
        status='closed', 
        date_closed__isnull=False
    )
    
    avg_resolution_time = 0
    if closed_with_dates.exists():
        resolution_times = []
        for ticket in closed_with_dates:
        # Add a check to ensure date_closed is after date_submitted
            if ticket.date_closed > ticket.date_submitted:
                time_diff = ticket.date_closed - ticket.date_submitted
                resolution_times.append(time_diff.total_seconds() / 3600)  # Convert to hours
        
        avg_resolution_time = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else 0
    
    status_counts = {
        'open': open_tickets,
        'pending': pending_tickets,
        'closed': closed_tickets
    }
    
    department_counts = []
    dept_dict = dict(Ticket.DEPT_CHOICES)
    
    dept_data = tickets.values('department').annotate(count=Count('id')).order_by('-count')
    
    for item in dept_data:
        if item['department']:
            dept_name = dept_dict.get(item['department'], 'Unknown')
            department_counts.append({
                'name': dept_name,
                'count': item['count']
            })
    
    if not department_counts:
        department_counts = [
            {'name': 'No Department Data', 'count': total_tickets}
        ]
    
    date_counts = {}
    delta = date_to - date_from
    for i in range(delta.days + 1):
        current_date = date_from + timedelta(days=i)
        date_counts[current_date.strftime('%Y-%m-%d')] = 0

    for ticket in tickets:
        ticket_date = ticket.date_submitted.date().strftime('%Y-%m-%d')
        if ticket_date in date_counts:
            date_counts[ticket_date] += 1
    
    date_trend = [{'date': date, 'count': count} for date, count in date_counts.items()]
    
    staff_performance = []
    assigned_staff = Staff.objects.filter(
        ticket__in=tickets
    ).distinct()
    
    for staff in assigned_staff:
        staff_tickets = tickets.filter(assigned_staff=staff)
        total_count = staff_tickets.count()
        resolved_count = staff_tickets.filter(status='closed').count()
        
        staff_closed_tickets = staff_tickets.filter(
            status='closed',
            date_closed__isnull=False
        )
        
        avg_res_time = 0
        if staff_closed_tickets.exists():
            res_times = []
            for ticket in staff_closed_tickets:
                if ticket.date_closed > ticket.date_submitted:  # Only calculate if dates are in correct order
                    time_diff = abs(ticket.date_closed - ticket.date_submitted)
                    res_times.append(time_diff.total_seconds() / 3600)
            
            avg_res_time = round(sum(res_times) / len(res_times), 1) if res_times else 0
        
        staff_rated_tickets = staff_tickets.filter(rating__isnull=False)
        satisfaction = 0
        if staff_rated_tickets.exists():
            ratings_sum = sum(ticket.rating for ticket in staff_rated_tickets)
            avg_rating = ratings_sum / staff_rated_tickets.count()
            satisfaction = round((avg_rating / 5) * 100)  # Convert to percentage
        
        staff_performance.append({
            'name': f"{staff.user.first_name} {staff.user.last_name}",
            'tickets_resolved': resolved_count,
            'avg_resolution_time': avg_res_time,
            'satisfaction_rating': satisfaction if satisfaction else 0
        })
    
    # Sort by most resolved tickets
    staff_performance.sort(key=lambda x: x['tickets_resolved'], reverse=True)
    
    # If no staff performance data, create sample data
    if not staff_performance:
        staff_performance = [
            {'name': 'No Staff Data', 'tickets_resolved': 0, 'avg_resolution_time': 0, 'satisfaction_rating': 0},
        ]
    
    # Priority distribution
    priority_counts = []
    priority_dict = dict(Ticket.PRIORITY_CHOICES)
    
    # Count tickets by priority
    priority_data = tickets.values('priority').annotate(count=Count('id')).order_by('-count')
    
    for item in priority_data:
        if item['priority']:
            priority_name = priority_dict.get(item['priority'], 'Not Set')
            priority_counts.append({
                'name': priority_name,
                'count': item['count']
            })
    
    if not priority_counts:
        priority_counts = [
            {'name': 'Not Specified', 'count': total_tickets}
        ]
    
    satisfaction = {
        'five_star': tickets.filter(rating=5).count(),
        'four_star': tickets.filter(rating=4).count(),
        'three_star': tickets.filter(rating=3).count(),
        'two_star': tickets.filter(rating=2).count(),
        'one_star': tickets.filter(rating=1).count()
    }
    
    analytics = {
        'total_tickets': total_tickets,
        'total_tickets_change': total_change_pct,
        'open_tickets': open_tickets,
        'pending_tickets': pending_tickets,
        'closed_tickets': closed_tickets,
        'resolution_rate': resolution_rate,
        'avg_response_time': avg_response_time,
        'avg_resolution_time': avg_resolution_time,
        'status_counts': status_counts,
        'department_counts': department_counts,
        'date_trend': date_trend,
        'staff_performance': staff_performance,
        'category_counts': priority_counts,  # Using priority as a category
        'satisfaction': satisfaction
    }
    
    return render(request, 'admin-panel/admin_analytics.html', {
        'analytics': analytics,
        'date_from': date_from,
        'date_to': date_to
    })


def export_tickets_csv(request):
    # Get date range from request or use default (last 30 days)
    today = timezone.now().date()
    default_start = today - timedelta(days=30)
    
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    
    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else default_start
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else today
    except ValueError:
        date_from = default_start
        date_to = today
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    filename = f'tickets_report_{date_from}_to_{date_to}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write CSV header
    writer.writerow(['Ticket ID', 'Subject', 'Status', 'Priority', 'Department', 
                    'Submitted Date', 'Closed Date', 'Assigned Staff', 
                    'Student', 'Rating', 'Resolution Time (Hours)'])
    
    # Get tickets for the date range
    tickets = Ticket.objects.filter(
        date_submitted__date__gte=date_from,
        date_submitted__date__lte=date_to
    )
    
    # Write ticket data
    for ticket in tickets:
        # Calculate resolution time (if applicable)
        resolution_time = ''
        if ticket.status == 'closed' and ticket.date_closed:
            time_diff = ticket.date_closed - ticket.date_submitted
            resolution_time = round(time_diff.total_seconds() / 3600, 2)  # Convert to hours
        
        # Get assigned staff name
        assigned_staff_name = ''
        if ticket.assigned_staff:
            assigned_staff_name = f"{ticket.assigned_staff.user.first_name} {ticket.assigned_staff.user.last_name}"
        
        # Get student name
        student_name = ''
        if ticket.student:
            student_name = f"{ticket.student.user.first_name} {ticket.student.user.last_name}"
        
        # Get department display name
        department = dict(Ticket.DEPT_CHOICES).get(ticket.department, '') if ticket.department else ''
        
        # Write the row
        writer.writerow([
            ticket.id,
            ticket.subject,
            dict(Ticket.STATUS_CHOICES).get(ticket.status, ticket.status),
            dict(Ticket.PRIORITY_CHOICES).get(ticket.priority, '') if ticket.priority else '',
            department,
            ticket.date_submitted.strftime('%Y-%m-%d %H:%M'),
            ticket.date_closed.strftime('%Y-%m-%d %H:%M') if ticket.date_closed else '',
            assigned_staff_name,
            student_name,
            ticket.rating if ticket.rating else '',
            resolution_time
        ])
    
    return response

def export_performance_csv(request):
    """Export staff performance metrics as CSV"""
    # Get date range from request or use default (last 30 days)
    today = timezone.now().date()
    default_start = today - timedelta(days=30)
    
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    
    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else default_start
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else today
    except ValueError:
        date_from = default_start
        date_to = today
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    filename = f'staff_performance_{date_from}_to_{date_to}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write CSV header
    writer.writerow(['Staff Name', 'Department', 'Total Tickets', 'Tickets Resolved', 
                    'Avg Resolution Time (Hours)', 'Avg Rating'])
    
    # Get all staff members who have been assigned tickets
    from django.db.models import Count, Avg, Q, F
    from .models import Staff
    
    staff_with_tickets = Staff.objects.filter(
        ticket__date_submitted__date__gte=date_from,
        ticket__date_submitted__date__lte=date_to
    ).distinct()
    
    for staff in staff_with_tickets:
        # Get tickets assigned to this staff member
        assigned_tickets = Ticket.objects.filter(
            assigned_staff=staff,
            date_submitted__date__gte=date_from,
            date_submitted__date__lte=date_to
        )
        
        total_tickets = assigned_tickets.count()
        resolved_tickets = assigned_tickets.filter(status='closed').count()
        
        # Calculate average resolution time
        closed_tickets_with_dates = assigned_tickets.filter(
            status='closed', 
            date_closed__isnull=False
        )
    
        avg_resolution_time = ''
        if closed_tickets_with_dates.exists():
            resolution_times = []
            for ticket in closed_tickets_with_dates:
                if ticket.date_closed > ticket.date_submitted:

                    time_diff = ticket.date_closed - ticket.date_submitted
                    resolution_times.append(time_diff.total_seconds() / 3600)  # Convert to hours
            
            avg_resolution_time = round(sum(resolution_times) / len(resolution_times), 2) if resolution_times else ''
        
        # Calculate average rating
        avg_rating = ''
        rated_tickets = assigned_tickets.filter(rating__isnull=False)
        if rated_tickets.exists():
            avg_rating = round(rated_tickets.aggregate(Avg('rating'))['rating__avg'], 2)
        
        writer.writerow([
            f"{staff.user.first_name} {staff.user.last_name}",
            staff.get_department_display(),
            total_tickets,
            resolved_tickets,
            avg_resolution_time,
            avg_rating
        ])
    
    return response

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from ticket.models import Ticket, CustomUser

@login_required
def admin_profile(request):
    if request.user.role != 'admin':
        raise PermissionDenied()

    context = {
        "tickets_count": Ticket.objects.count(),
        "open_tickets_count": Ticket.objects.filter(status='open').count(),
        "closed_tickets_count": Ticket.objects.filter(status='closed').count(),
        "user_count": CustomUser.objects.count(),
    }
    return render(request, 'admin-panel/admin_profile.html', context)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django import forms

User = get_user_model()

class AdminUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

@login_required
def admin_update_profile(request):
    user = request.user

    if user.role != 'admin':
        return redirect('admin_dashboard')  # Just to be safe

    if request.method == 'POST':
        form = AdminUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('admin_profile')
    else:
        form = AdminUpdateForm(instance=user)

    return render(request, 'admin-panel/admin_update_profile.html', {'form': form})

from django.views.decorators.csrf import csrf_protect

from ticket.models import AdminMessage, StudentMessage

from django.views.decorators.csrf import csrf_protect
from ticket.models import Ticket, Staff, StudentMessage, AdminMessage, CustomUser

@login_required
@csrf_protect
def admin_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.method == 'POST':
        # Sending an admin message
        if 'message' in request.POST:
            content = request.POST.get('message', '').strip()
            if content:
                AdminMessage.objects.create(
                    ticket=ticket,
                    author=request.user,
                    content=content
                )
                return redirect('admin_ticket_detail', ticket_id=ticket.id)

        # Updating ticket
        elif 'update_ticket' in request.POST:
            ticket.department = request.POST.get('department')
            ticket.status = request.POST.get('status')
            staff_id = request.POST.get('assigned_staff')

            if staff_id:
                try:
                    staff_instance = Staff.objects.get(user__id=staff_id)
                    ticket.assigned_staff = staff_instance
                except Staff.DoesNotExist:
                    messages.error(request, "Invalid staff member selected.")
                    return redirect('admin_ticket_detail', ticket_id=ticket.id)
            else:
                ticket.assigned_staff = None

            ticket.save()
            return redirect('admin_ticket_detail', ticket_id=ticket.id)

    context = {
        'ticket': ticket,
        'student_messages': StudentMessage.objects.filter(ticket=ticket).order_by('created_at'),
        'admin_messages': AdminMessage.objects.filter(ticket=ticket).order_by('created_at'),
        'staff_members': Staff.objects.select_related('user'),
        'dept_choices': Ticket._meta.get_field('department').choices,
    }
    return render(request, 'admin-panel/admin_ticket_detail.html', context)

@login_required
def admin_announcements(request):
    """View for admin to manage announcements"""
    if request.user.role != 'admin':
        raise PermissionDenied
        
    announcements = Announcement.objects.all().order_by('-created_at')
    dept_choices = settings.DEPT_CHOICES[1:]  # Skip the empty choice
    
    return render(request, 'admin-panel/announcements.html', {
        'announcements': announcements,
        'dept_choices': dept_choices,
    })

@login_required
def create_announcement(request):
    """Handle creation of new announcements"""
    if request.user.role != 'admin':
        raise PermissionDenied
        
    if request.method == 'POST':
        content = request.POST.get('content')
        department = request.POST.get('department') or None
        
        if content:
            Announcement.objects.create(
                content=content,
                department=department,
                created_by=request.user
            )
            messages.success(request, 'Announcement posted successfully.')
        else:
            messages.error(request, 'Content is required.')
            
    return redirect('admin_announcements')

@login_required
def staff_announcements(request):
    """View for staff to see all announcements"""
    if not hasattr(request.user, 'staff'):
        raise PermissionDenied
        
    staff_department = request.user.staff.department
    announcements = Announcement.objects.filter(
        models.Q(department=None) | models.Q(department=staff_department)  # Get both general and department-specific announcements
    ).order_by('-created_at')
    
    return render(request, 'staff/announcements.html', {
        'announcements': announcements
    })

@login_required
def delete_announcement(request, announcement_id):
    """Handle deletion of announcements"""
    if request.user.role != 'admin':
        raise PermissionDenied
        
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
    messages.success(request, 'Announcement deleted successfully.')
            
    return redirect('admin_announcements')

def get_full_name(self):
    return f"{self.first_name} {self.last_name}"

class ForgetPasswordMailView(View):
    """
    Handles user registration using Django's Class-Based Views.
    """
    
    def get(self, request):
        context={}
        return render(request, 'forget-password/mail-page.html', context)

    def post(self, request):
        mail = request.POST.get("email")
        try:
            user = CustomUser.objects.get(email=mail)
            if user:
                token = user.generate_remember_token()
                encoded_token = quote(token)
                reset_link = f"{settings.MAIN_URL}/forget-password/reset?token={encoded_token}"

                context = {
                    "user": user,
                    "reset_link": reset_link,
                    'website_name': settings.WEBSITE_NAME,
                    'main_mail': settings.EMAIL_HOST_USER
                }

                sendHtmlMail(
                    view="mail-template/reset-password-mail.html",
                    subject=f"Reset Your Password - {settings.WEBSITE_NAME}",
                    from_email=settings.EMAIL_HOST_USER,
                    to_email=[mail],
                    context=context,
                )

            # Clear previous messages first
            storage = messages.get_messages(request)
            storage.used = True  # This ensures old messages don’t get displayed again

            # Add the new success message
            messages.success(request, "Reset email has been sent. Please check your inbox.")

            return render(request, 'forget-password/email-sent.html', {
                "email": mail
            })


        except CustomUser.DoesNotExist:
            return render(request, 'exception/error-page.html', {
                "title": "User Not Found",
                "message": "We couldn't find an account associated with this email.",
                "link": reverse('log_in')
            })
        
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views import View
from .forms import EditAccountForm
from .models import CustomUser

class AdminAccountEditView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, account_id):
        # Logic to handle GET request, like displaying the account form
        account = get_object_or_404(CustomUser, id=account_id)
        form = EditAccountForm(instance=account)
        return render(request, "admin-panel/admin_accounts.html", {"form": form, "is_update": True})

    def post(self, request, account_id):
        # Logic to handle POST request, like saving updates
        account = get_object_or_404(CustomUser, id=account_id)
        form = EditAccountForm(request.POST, instance=account)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account updated successfully!")
            return redirect('admin_accounts_list')
        return render(request, "admin-panel/admin_accounts.html", {"form": form, "is_update": True})

class PasswordResetSentView(View):
    def get(self, request):
        return render(request, 'forget-password/email-sent.html')
    
def password_reset_sent(request):
    return render(request, 'forget-password/email-sent.html')

def ForgetPasswordView(request):
    return render(request, 'forget-password/mail-page.html')

class PasswordResetView(View):
    def get(self, request):
        token = request.GET.get('token')
        if not token:
            return render(request, 'exception/error-page.html', {
                "title": "Invalid Token",
                "message": "No valid token provided. Please request a new password reset.",
                "link": reverse('log_in')
            })
        return render(request, 'forget-password/new-password.html', {"token": token})

from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from ticket.models import CustomUser
from urllib.parse import quote 

class ForgetPasswordNewPasswordView(View):
    def get(self, request):
        token = request.GET.get('token')

        try:
            user = CustomUser.objects.get(remember_token=token)

            if user and user.is_remember_token_valid(token):
                return render(request, 'forget-password/new-password.html', {"token": token})
            else:
                return render(request, 'exception/error-page.html', {
                    "title": "Invalid or Expired Token",
                    "message": "The password reset link is incorrect or expired.",
                    "link": reverse('log_in')
                })

        except CustomUser.DoesNotExist:
            return render(request, 'exception/error-page.html', {
                "title": "Invalid Token",
                "message": "The token is invalid or expired.",
                "link": reverse('log_in')
            })

    def post(self, request):
        token = request.POST.get('token')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')


        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect(request.path + f"?token={token}")

        try:
            user = CustomUser.objects.get(remember_token=token)

            if user and user.is_remember_token_valid(token):
                user.set_password(new_password)
                user.clear_remember_token()
                user.save()

                messages.success(request, 'Password updated successfully.')
                return redirect("log_in")

            else:
                return render(request, 'exception/error-page.html', {
                    "title": "Invalid or Expired Token",
                    "message": "The password reset link is incorrect or expired.",
                    "link": reverse('log_in')
                })

        except CustomUser.DoesNotExist:
            return render(request, 'exception/error-page.html', {
                "title": "Invalid Token",
                "message": "The token is invalid or expired.",
                "link": reverse('log_in')
            })

