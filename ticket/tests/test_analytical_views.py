import datetime
from unittest.mock import patch
from io import StringIO
import csv

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from ticket.models import Ticket, Staff, Student, AdminMessage, StudentMessage, StaffMessage, CustomUser

class AnalyticsViewsTest(TestCase):
    """Tests for the analytics dashboard and export views."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = CustomUser.objects.create_user(
            username='admin_user',
            email='admin@university.edu',
            password='adminpassword',
            role='admin',
            first_name='Admin',
            last_name='User'
        )
        
        # Create staff user
        self.staff_user = CustomUser.objects.create_user(
            username='staff_user',
            email='staff@university.edu',
            password='staffpassword',
            role='staff',
            first_name='Staff',
            last_name='User'
        )
        self.staff = Staff.objects.create(
            user=self.staff_user,
            department='business',
            role='IT Support'
        )
        
        # Create student user
        self.student_user = CustomUser.objects.create_user(
            username='student_user',
            email='student@university.edu',
            password='studentpassword',
            role='student',
            first_name='Student',
            last_name='User'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            department='business',
            program='MBA',
            year_of_study=2
        )
        
        # Create tickets with different statuses and dates
        self.now = timezone.now()
        self.one_day_ago = self.now - datetime.timedelta(days=1)
        self.two_days_ago = self.now - datetime.timedelta(days=2)
        self.five_days_ago = self.now - datetime.timedelta(days=5)
        
        # Open ticket
        self.open_ticket = Ticket.objects.create(
            subject='Open Test Ticket',
            description='This is an open test ticket',
            status='open',
            student=self.student,
            department='business',
            priority='normal',
            date_submitted=self.two_days_ago
        )
        
        # Pending ticket
        self.pending_ticket = Ticket.objects.create(
            subject='Pending Test Ticket',
            description='This is a pending test ticket',
            status='pending',
            student=self.student,
            assigned_staff=self.staff,
            department='arts_humanities',
            priority='urgent',
            date_submitted=self.five_days_ago
        )
        
        # Closed ticket with rating
        self.closed_ticket = Ticket.objects.create(
            subject='Closed Test Ticket',
            description='This is a closed test ticket',
            status='closed',
            student=self.student,
            assigned_staff=self.staff,
            closed_by=self.staff,
            department='law',
            priority='low',
            date_submitted=self.five_days_ago,
            date_closed=self.one_day_ago,
            rating=4
        )
        
        # Messages for the tickets
        AdminMessage.objects.create(
            ticket=self.open_ticket,
            author=self.student_user,
            content='Initial message from student',
            created_at=self.open_ticket.date_submitted
        )
        
        AdminMessage.objects.create(
            ticket=self.pending_ticket,
            author=self.student_user,
            content='Initial message from student',
            created_at=self.pending_ticket.date_submitted
        )
        
        # Staff response to the pending ticket
        AdminMessage.objects.create(
            ticket=self.pending_ticket,
            author=self.staff_user,
            content='Response from staff',
            created_at=self.pending_ticket.date_submitted + datetime.timedelta(hours=4)
        )
        
        AdminMessage.objects.create(
            ticket=self.closed_ticket,
            author=self.student_user,
            content='Initial message from student',
            created_at=self.closed_ticket.date_submitted
        )
        
        # Staff response to the closed ticket
        AdminMessage.objects.create(
            ticket=self.closed_ticket,
            author=self.staff_user,
            content='Response from staff',
            created_at=self.closed_ticket.date_submitted + datetime.timedelta(hours=2)
        )
        
        # Login the admin user
        self.client = Client()
        self.client.login(username='admin_user', password='adminpassword')
    
    def test_analytics_dashboard_access(self):
        """Test that the analytics dashboard can be accessed by admin."""
        response = self.client.get(reverse('admin_analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin-panel/analytics.html')
    
    def test_analytics_dashboard_denied_for_non_admin(self):
        """Test that non-admin users cannot access the analytics dashboard."""
        # Login as staff
        self.client.logout()
        self.client.login(username='staff_user', password='staffpassword')
        
        response = self.client.get(reverse('admin_analytics'))
        self.assertNotEqual(response.status_code, 200)  # Should be 403 Forbidden or redirect
    
    def test_analytics_dashboard_data(self):
        """Test that the analytics dashboard contains the correct data."""
        response = self.client.get(reverse('admin_analytics'))
        
        # Check context data
        analytics = response.context['analytics']
        Ticket.objects.create(
        subject='Additional Business Ticket',
        description='This is another business department ticket',
        status='open',
        student=self.student,
        department='business',
        priority='normal',
        date_submitted=timezone.now() - datetime.timedelta(days=1)
    )
        # Basic ticket counts
        self.assertEqual(analytics['total_tickets'], 3)
        self.assertEqual(analytics['open_tickets'], 1)
        self.assertEqual(analytics['pending_tickets'], 1)
        self.assertEqual(analytics['closed_tickets'], 1)
        
        # Status counts
        self.assertEqual(analytics['status_counts']['open'], 1)
        self.assertEqual(analytics['status_counts']['pending'], 1)
        self.assertEqual(analytics['status_counts']['closed'], 1)
        
        # Ensure resolution rate is calculated correctly (1/3 = 33.3%)
        self.assertAlmostEqual(analytics['resolution_rate'], 33.3, delta=0.1)
        
        # Ensure department counts are correct
        dept_counts = {item['name']: item['count'] for item in analytics['department_counts']}
        self.assertEqual(dept_counts.get('Business'), 2)  # Business department tickets
        self.assertEqual(dept_counts.get('Law'), 1)  # Law department tickets
        
        # Verify staff performance data exists
        self.assertTrue(len(analytics['staff_performance']) > 0)
        
        # Ensure avg resolution time is positive and reasonable
        self.assertGreaterEqual(analytics['avg_resolution_time'], 0)
    
    def test_export_tickets_csv(self):
        """Test the export tickets CSV functionality."""
        response = self.client.get(reverse('export_tickets_csv'))
        
        # Check response is a CSV file
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertTrue('attachment; filename=' in response['Content-Disposition'])
        
        # Parse the CSV content
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        rows = list(reader)
        
        # Check header row
        self.assertEqual(len(rows), 4)  # Header + 3 ticket rows
        self.assertTrue('Ticket ID' in rows[0])
        self.assertTrue('Subject' in rows[0])
        self.assertTrue('Status' in rows[0])
        
        # Check data rows
        ticket_subjects = [row[1] for row in rows[1:]]  # Subject is in column 1
        self.assertIn('Open Test Ticket', ticket_subjects)
        self.assertIn('Pending Test Ticket', ticket_subjects)
        self.assertIn('Closed Test Ticket', ticket_subjects)
    
    def test_export_performance_csv(self):
        """Test the export performance CSV functionality."""
        response = self.client.get(reverse('export_performance_csv'))
        
        # Check response is a CSV file
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertTrue('attachment; filename=' in response['Content-Disposition'])
        
        # Parse the CSV content
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        rows = list(reader)
        
        # Check header row
        self.assertTrue(len(rows) >= 2)  # Header + at least 1 staff row
        self.assertTrue('Staff Name' in rows[0])
        self.assertTrue('Department' in rows[0])
        self.assertTrue('Total Tickets' in rows[0])
        
        # Check data row for the staff member
        staff_names = [row[0] for row in rows[1:]]
        self.assertIn('Staff User', staff_names)
    
    def test_date_filtering(self):
        """Test that date filtering works correctly."""
        today = timezone.now().date()
        yesterday = today - datetime.timedelta(days=1)
        
        url = reverse('admin_analytics') + f'?date_from={yesterday}&date_to={today}'
        response = self.client.get(url)
        
        analytics = response.context['analytics']
        
   
        self.assertTrue(analytics['total_tickets'] > 0)
    
    def test_avg_response_time_calculation(self):
        """Test that average response time is calculated correctly."""
        response = self.client.get(reverse('admin_analytics'))
        analytics = response.context['analytics']
       
        self.assertGreaterEqual(analytics['avg_response_time'], 0)
        self.assertLessEqual(analytics['avg_response_time'], 24)  # Response was within 24 hours