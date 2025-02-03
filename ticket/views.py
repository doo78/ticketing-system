from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from .models import Ticket, Staff
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from ticket.forms import LogInForm  

# Create your views here.

def home(request):
    return render(request, 'home.html')


class LogInView(View):
    """Display login screen and handle user login."""
    
    http_method_names = ['get', 'post']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.redirect_url = settings.REDIRECT_URL_WHEN_LOGGED_IN 

    def get(self, request):
        """Display log in template."""
        next_page = request.GET.get('next', '')  
        return self.render(request, next_page)

    def post(self, request):
        """Handle log in attempt."""
        form = LogInForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None and user.is_active:
                login(request, user)
                return redirect(self.redirect_url)  
            else:
                messages.error(request, "The credentials provided were invalid!")
        return self.render(request)  

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
   
