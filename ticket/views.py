from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views import View
from django.urls import reverse
from django.conf import settings
from ticket.forms import LogInForm  

# Create your views here.

def view_tickets(request):
    return render(request, 'view_tickets.html')


def home(request):
    return render(request, 'home.html')


class TicketListView(View):
    """Loads the tickets corresponding to the list type"""

    def get(self, request, list_type):
        if list_type == 'open':
            page_heading = "Open Tickets"
            table_headers = ["ID", "Email", "Subject", "Date Submitted"]

        elif list_type == 'pending':
            page_heading = "Pending Tickets"
            table_headers = ["ID", "Email", "Subject", "Date Submitted", "Date Last Updated", "Assigned Staff"]

        elif list_type == 'closed':
            page_heading = "Closed Tickets"
            table_headers = ["ID", "Email", "Subject", "Date Submitted", "Date Closed", "Assigned Staff", "Closed By"]

        else:
            return render(request, '404.html')  

        context = {
            'page_heading': page_heading,
            'table_headers': table_headers,
            'list_type': list_type
        }

        return render(request, 'view_tickets.html', context)

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

