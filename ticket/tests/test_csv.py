import datetime
from io import StringIO
import csv

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from ticket.models import Ticket, Staff, Student, CustomUser

class CSVExportTest(TestCase):
    """Tests for the CSV export functionality."""
    
    def setUp(self):
        """Set up test data for CSV export testing."""
        # Create admin user
        self.admin_user = CustomUser.objects.create_user(
            username='csv_admin',
            email='csv_admin@university.edu',
            password='adminpassword',
            role='admin',
            first_name='CSV',
            last_name='Admin'
        )
        
        # Create staff users
        self.staff_user1 = CustomUser.objects.create_user(
            username='csv_staff1',
            email='csv_staff1@university.edu',
            password='staffpassword',
            role='staff',
            first_name='CSV',
            last_name='Staff1'
        )
        self.staff1 = Staff.objects.create(
            user=self.staff_user1,
            department='business',
            role='IT Support'
        )
        
        self.staff_user2 = CustomUser.objects.create_user(
            username='csv_staff2',
            email='csv_staff2@university.edu',
            password='staffpassword',
            role='staff',
            first_name='CSV',
            last_name='Staff2'
        )
        self.staff2 = Staff.objects.create(
            user=self.staff_user2,
            department='law',
            role='Legal Support'
        )
        
        # Create student user
        self.student_user = CustomUser.objects.create_user(
            username='csv_student',
            email='csv_student@university.edu',
            password='studentpassword',
            role='student',
            first_name='CSV',
            last_name='Student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            department='business',
            program='MBA',
            year_of_study=2
        )
        
        # Create tickets with different statuses, departments, and assignments
        self.now = timezone.now()
        
        # Create 10 tickets with various properties
        ticket_data = [
            {
                'subject': 'Business Ticket 1',
                'status': 'open',
                'department': 'business',
                'priority': 'low',
                'assigned_staff': None,
                'days_ago': 10,
                'hours_to_close': None,
                'rating': None
            },
            {
                'subject': 'Business Ticket 2',
                'status': 'pending',
                'department': 'business',
                'priority': 'normal',
                'assigned_staff': self.staff1,
                'days_ago': 8,
                'hours_to_close': None,
                'rating': None
            },
            {
                'subject': 'Business Ticket 3',
                'status': 'closed',
                'department': 'business',
                'priority': 'urgent',
                'assigned_staff': self.staff1,
                'days_ago': 7,
                'hours_to_close': 24,
                'rating': 5
            },
            {
                'subject': 'Law Ticket 1',
                'status': 'open',
                'department': 'law',
                'priority': 'normal',
                'assigned_staff': None,
                'days_ago': 6,
                'hours_to_close': None,
                'rating': None
            },
            {
                'subject': 'Law Ticket 2',
                'status': 'pending',
                'department': 'law',
                'priority': 'urgent',
                'assigned_staff': self.staff2,
                'days_ago': 5,
                'hours_to_close': None,
                'rating': None
            },
            {
                'subject': 'Law Ticket 3',
                'status': 'closed',
                'department': 'law',
                'priority': 'low',
                'assigned_staff': self.staff2,
                'days_ago': 4,
                'hours_to_close': 12,
                'rating': 4
            },
            {
                'subject': 'Nursing Ticket',
                'status': 'closed',
                'department': 'nursing',
                'priority': 'normal',
                'assigned_staff': self.staff1,
                'days_ago': 3,
                'hours_to_close': 48,
                'rating': 3
            },
            {
                'subject': 'Dentistry Ticket',
                'status': 'closed',
                'department': 'dentistry',
                'priority': 'urgent',
                'assigned_staff': self.staff2,
                'days_ago': 2,
                'hours_to_close': 6,
                'rating': 5
            },
            {
                'subject': 'Arts Ticket',
                'status': 'open',
                'department': 'arts_humanities',
                'priority': 'low',
                'assigned_staff': None,
                'days_ago': 1,
                'hours_to_close': None,
                'rating': None
            },
            {
                'subject': 'Long Resolution Ticket',
                'status': 'closed',
                'department': 'business',
                'priority': 'urgent',
                'assigned_staff': self.staff1,
                'days_ago': 15,
                'hours_to_close': 120,  # 5 days to resolve
                'rating': 2
            }
        ]
        
        self.tickets = []
        for data in ticket_data:
            date_submitted = self.now - datetime.timedelta(days=data['days_ago'])
            
            date_closed = None
            if data['hours_to_close']:
                date_closed = date_submitted + datetime.timedelta(hours=data['hours_to_close'])
            
            ticket = Ticket.objects.create(
                subject=data['subject'],
                description=f"Description for {data['subject']}",
                status=data['status'],
                student=self.student,
                assigned_staff=data['assigned_staff'],
                closed_by=data['assigned_staff'] if data['status'] == 'closed' else None,
                department=data['department'],
                priority=data['priority'],
                date_submitted=date_submitted,
                date_closed=date_closed,
                rating=data['rating']
            )
            self.tickets.append(ticket)
        
        # Login as admin
        self.client = Client()
        self.client.login(username='csv_admin', password='adminpassword')
    
    def test_export_tickets_csv_content(self):
        """Test that the exported tickets CSV contains all expected data."""
        response = self.client.get(reverse('export_tickets_csv'))
        
        # Check response is a CSV file
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertTrue('attachment; filename=' in response['Content-Disposition'])
        
        # Parse the CSV content
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        rows = list(reader)
        
        # Check header row
        self.assertEqual(len(rows), 11)  # Header + 10 ticket rows
        
        # Check header columns
        header = rows[0]
        expected_headers = [
            'Ticket ID', 'Subject', 'Status', 'Priority', 'Department', 
            'Submitted Date', 'Closed Date', 'Assigned Staff', 
            'Student', 'Rating', 'Resolution Time (Hours)'
        ]
        for expected in expected_headers:
            self.assertIn(expected, header)
        
        # Get column indices
        subject_idx = header.index('Subject')
        status_idx = header.index('Status')
        priority_idx = header.index('Priority')
        department_idx = header.index('Department')
        rating_idx = header.index('Rating')
        resolution_time_idx = header.index('Resolution Time (Hours)')
        
        # Check data rows
        data_rows = rows[1:]
        
        # Check all tickets are included
        subjects = [row[subject_idx] for row in data_rows]
        for ticket in self.tickets:
            self.assertIn(ticket.subject, subjects)
        
        # Check status formatting
        statuses = [row[status_idx] for row in data_rows]
        self.assertIn('Open', statuses)
        self.assertIn('Pending', statuses)
        self.assertIn('Closed', statuses)
        
        # Check priority formatting
        priorities = [row[priority_idx] for row in data_rows]
        self.assertIn('Low', priorities)
        self.assertIn('Normal', priorities)
        self.assertIn('Urgent', priorities)
        
        # Check department formatting
        departments = [row[department_idx] for row in data_rows]
        self.assertIn('Business', departments)
        self.assertIn('Law', departments)
        
        # Check ratings
        for row in data_rows:
            if row[status_idx] == 'Closed':
                self.assertTrue(row[rating_idx].strip() != '')
            
            # Check resolution time for closed tickets
            if row[status_idx] == 'Closed':
                self.assertTrue(float(row[resolution_time_idx]) > 0)
                
                # Find this ticket in our data to verify the resolution time
                ticket_data = next((t for t in ticket_data if t['subject'] == row[subject_idx]), None)
                if ticket_data and ticket_data['hours_to_close']:
                    self.assertAlmostEqual(float(row[resolution_time_idx]), 
                                          ticket_data['hours_to_close'], 
                                          delta=0.1)
    
    def test_export_performance_csv_content(self):
        """Test that the exported performance CSV contains all expected data."""
        response = self.client.get(reverse('export_performance_csv'))
        
        # Check response is a CSV file
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertTrue('attachment; filename=' in response['Content-Disposition'])
        
        # Parse the CSV content
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        rows = list(reader)