import datetime
from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse

from ticket.models import Ticket, Staff, Student, AdminMessage, StudentMessage, StaffMessage, CustomUser
from ticket.views import analytics_dashboard

class AnalyticsCalculationsTest(TestCase):
    """Tests for the analytics calculation logic."""
    
    def setUp(self):
        """Set up test data with very specific timing for predictable calculations."""
        # Create admin user
        self.admin_user = CustomUser.objects.create_user(
            username='admin_calc',
            email='admin_calc@university.edu',
            password='adminpassword',
            role='admin',
            first_name='Admin',
            last_name='Calculator'
        )
        
        # Create staff user
        self.staff_user = CustomUser.objects.create_user(
            username='staff_calc',
            email='staff_calc@university.edu',
            password='staffpassword',
            role='staff',
            first_name='Staff',
            last_name='Calculator'
        )
        self.staff = Staff.objects.create(
            user=self.staff_user,
            department='business',
            role='IT Support'
        )
        
        # Create student user
        self.student_user = CustomUser.objects.create_user(
            username='student_calc',
            email='student_calc@university.edu',
            password='studentpassword',
            role='student',
            first_name='Student',
            last_name='Calculator'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            department='business',
            program='MBA',
            year_of_study=2
        )
        
        # Create tickets with precise timing
        self.base_time = timezone.now().replace(microsecond=0)
        
        # Ticket 1: Closed after exactly 10 hours
        submission_time1 = self.base_time - datetime.timedelta(days=7)
        close_time1 = submission_time1 + datetime.timedelta(hours=10)
        
        self.ticket1 = Ticket.objects.create(
            subject='Calculation Test Ticket 1',
            description='This is a test ticket with 10 hour resolution time',
            status='closed',
            student=self.student,
            assigned_staff=self.staff,
            closed_by=self.staff,
            department='business',
            priority='normal',
            date_submitted=submission_time1,
            date_closed=close_time1,
            rating=5
        )
        
        # Staff responds after exactly 2 hours
        response_time1 = submission_time1 + datetime.timedelta(hours=2)
        
        # Messages for ticket 1
        AdminMessage.objects.create(
            ticket=self.ticket1,
            author=self.student_user,
            content='Initial message from student',
            created_at=submission_time1
        )
        
        AdminMessage.objects.create(
            ticket=self.ticket1,
            author=self.staff_user,
            content='Response from staff after 2 hours',
            created_at=response_time1
        )
        
        # Ticket 2: Closed after exactly 20 hours
        submission_time2 = self.base_time - datetime.timedelta(days=5)
        close_time2 = submission_time2 + datetime.timedelta(hours=20)
        
        self.ticket2 = Ticket.objects.create(
            subject='Calculation Test Ticket 2',
            description='This is a test ticket with 20 hour resolution time',
            status='closed',
            student=self.student,
            assigned_staff=self.staff,
            closed_by=self.staff,
            department='business',
            priority='urgent',
            date_submitted=submission_time2,
            date_closed=close_time2,
            rating=4
        )
        
        # Staff responds after exactly 4 hours
        response_time2 = submission_time2 + datetime.timedelta(hours=4)
        
        # Messages for ticket 2
        AdminMessage.objects.create(
            ticket=self.ticket2,
            author=self.student_user,
            content='Initial message from student',
            created_at=submission_time2
        )
        
        AdminMessage.objects.create(
            ticket=self.ticket2,
            author=self.staff_user,
            content='Response from staff after 4 hours',
            created_at=response_time2
        )
        
        # Setup RequestFactory for direct view testing
        self.factory = RequestFactory()
        
        # Login the admin user for view access
        self.client.login(username='admin_calc', password='adminpassword')
    
    def test_resolution_time_calculation(self):
        """Test that resolution time is calculated correctly."""
        # Use the client to make an actual request to the view
        response = self.client.get(reverse('admin_analytics'))
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Extract analytics from the response context
        analytics = response.context['analytics']
        
        # The average resolution time should be (10 + 20) / 2 = 15 hours
        # We allow a small delta for floating point precision
        self.assertAlmostEqual(analytics['avg_resolution_time'], 15.0, delta=0.1)
    
    def test_response_time_calculation(self):
        """Test that average response time is calculated correctly."""
        response = self.client.get(reverse('admin_analytics'))
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        analytics = response.context['analytics']
        
        # The average response time should be (2 + 4) / 2 = 3 hours
        self.assertAlmostEqual(analytics['avg_response_time'], 3.0, delta=0.1)
    
    def test_negative_resolution_time_prevention(self):
        """Test that negative resolution times are prevented."""
        # Create a ticket with date_closed before date_submitted (incorrect data)
        bad_ticket = Ticket.objects.create(
            subject='Bad Date Ticket',
            description='This ticket has incorrect dates',
            status='closed',
            student=self.student,
            assigned_staff=self.staff,
            department='business',
            priority='normal',
            date_submitted=self.base_time,
            date_closed=self.base_time - datetime.timedelta(hours=5),  # 5 hours before submission
            rating=3
        )
        
        # This would result in a -5 hour resolution time
        
        response = self.client.get(reverse('admin_analytics'))
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        analytics = response.context['analytics']
        
        # The average resolution time should still be positive
        # It should either exclude the bad ticket or handle it safely
        self.assertGreaterEqual(analytics['avg_resolution_time'], 0)
        
        # Clean up the bad ticket
        bad_ticket.delete()
    
    def test_department_distribution(self):
        """Test that department distribution is calculated correctly."""
        # Add a ticket from a different department
        Ticket.objects.create(
            subject='Law Department Ticket',
            description='This is a test ticket from the law department',
            status='open',
            student=self.student,  # We're using the same student for simplicity
            department='law',
            priority='normal',
            date_submitted=self.base_time - datetime.timedelta(days=1)
        )
        
        response = self.client.get(reverse('admin_analytics'))
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        analytics = response.context['analytics']
        
        # Check department counts
        dept_counts = {item['name']: item['count'] for item in analytics['department_counts']}
        
        # There should be 2 tickets for Business department
        self.assertEqual(dept_counts.get('Business'), 2)
        
        # There should be 1 ticket for Law department
        self.assertEqual(dept_counts.get('Law'), 1)


class TicketExpirationTest(TestCase):
    """Test the ticket expiration functionality."""
    
    def setUp(self):
        """Set up test data for expiration testing."""
        # Create student
        self.student_user = CustomUser.objects.create_user(
            username='expiration_student',
            email='expiration@university.edu',
            password='password',
            role='student',
            first_name='Expiration',
            last_name='Test'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            department='business',
            program='MBA',
            year_of_study=2
        )
        
        # Create an expired ticket (set expiration_date to past)
        self.now = timezone.now()
        past_date = self.now - datetime.timedelta(days=1)
        
        # Override the default expiration date which is set in the model
        self.expired_ticket = Ticket.objects.create(
            subject='Expired Ticket',
            description='This is an expired ticket',
            status='open',
            student=self.student,
            department='business',
            priority='normal',
            date_submitted=self.now - datetime.timedelta(days=31),  # 31 days ago
            expiration_date=past_date  # Expired yesterday
        )
    
    def test_ticket_auto_closes_on_expiration(self):
        """Test that tickets auto-close when they expire."""
        # When we save the ticket again, it should auto-close due to expiration
        self.expired_ticket.save()
        
        # Refresh from database
        self.expired_ticket.refresh_from_db()
        
        # Check that status is now closed
        self.assertEqual(self.expired_ticket.status, 'closed')
        
        # Check that date_closed is set
        self.assertIsNotNone(self.expired_ticket.date_closed)