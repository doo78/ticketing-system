from django.shortcuts import render
from django.views import View

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