from django.shortcuts import render

# Create your views here.

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
