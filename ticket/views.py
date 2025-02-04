from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import Ticket, Staff
from .forms import TicketForm


#------------------------------------STUDENT SECTION------------------------------------#
#USE THIS AFTER Student MODEL IS MADE
# @login_required
# def create_ticket(request):
#     if not hasattr(request.user, 'student'):
#         raise PermissionDenied("Only students can create tickets")
        
#     if request.method == 'POST':
#         form = TicketForm(request.POST, student=request.user.student)
#         if form.is_valid():
#             ticket = form.save()
#             messages.success(request, 'Your ticket has been submitted successfully. Check your email for more information.') 
#             return redirect('ticket_detail', pk=ticket.id)
#     else:
#         form = TicketForm(student=request.user.student)
    
#     return render(request, 'tickets/create_ticket.html', {
#         'form': form,
#     })

#THIS VERSION IS FOR TESTING - REAL VERSION ABOVE
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)  # removed student parameter
        if form.is_valid():
            ticket = form.save()
            messages.success(request, 'Your ticket has been submitted successfully. Ticket number: #{}'.format(ticket.id))
            return redirect('ticket_detail', pk=ticket.id)
    else:
        form = TicketForm()  # removed student parameter
    
    return render(request, 'student/create_ticket.html', {
        'form': form
    })

def ticket_list(request):
    return render(request, 'student/ticket_list.html')
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
            assigned_staff= request.user.staff
        ).exclude(status='closed').count(),
    }
    return render(request, 'staff/dashboard.html', context)

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
    
