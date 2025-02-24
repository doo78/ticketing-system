from django.test import TestCase, Client
from django.urls import reverse
from ticket.models import CustomUser, Student, Ticket, Message, Staff
from django.utils import timezone
from datetime import timedelta

class StudentDashboardTest(TestCase):
    def setUp(self):
        # Create a student user
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role='student'
        )
        self.student = Student.objects.create(
            user=self.user,
            department='business',
            program='Business Administration',
            year_of_study=2
        )
        
        # Create some test tickets
        self.open_ticket = Ticket.objects.create(
            student=self.student,
            subject='Initial Support Query',
            description='This is a test open ticket',
            department='business',
            status='open'
        )
        
        self.closed_ticket = Ticket.objects.create(
            student=self.student,
            subject='Resolved Issue',
            description='This is a test closed ticket',
            department='business',
            status='closed',
            date_closed=timezone.now()
        )
        
        # URLs
        self.login_url = reverse('log_in')
        self.dashboard_url = reverse('student_dashboard')
        self.create_ticket_url = reverse('create_ticket')
        self.ticket_detail_url = reverse('ticket_detail', args=[self.open_ticket.id])

    def test_dashboard_access_authenticated(self):
        """Test that authenticated students can access their dashboard"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student/dashboard.html')

    def test_dashboard_access_unauthenticated(self):
        """Test that unauthenticated users cannot access the dashboard"""
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(response, f'/login/?next={self.dashboard_url}')

    def test_dashboard_content(self):
        """Test that dashboard shows correct ticket counts and information"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertContains(response, 'Initial Support Query')
        self.assertContains(response, 'Resolved Issue')
        self.assertEqual(len(response.context['open_tickets']), 1)
        self.assertEqual(len(response.context['closed_tickets']), 1)

    def test_create_ticket_get(self):
        """Test the ticket creation form display"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.create_ticket_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student/create_ticket.html')

    def test_create_ticket_post_success(self):
        """Test successful ticket creation"""
        self.client.login(username='testuser', password='testpass123')
        ticket_data = {
            'subject': 'New Test Ticket',
            'description': 'This is a new test ticket',
            'department': 'business'
        }
        response = self.client.post(self.create_ticket_url, ticket_data)
        self.assertRedirects(response, self.dashboard_url)
        
        # Verify ticket was created
        self.assertTrue(Ticket.objects.filter(subject='New Test Ticket').exists())
        
        # Check success message
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any(message.message.startswith('Your ticket #') for message in messages))

    def test_create_ticket_post_invalid(self):
        """Test ticket creation with invalid data"""
        self.client.login(username='testuser', password='testpass123')
        ticket_data = {
            'subject': '',  # Subject is required
            'description': 'This is a new test ticket',
            'department': 'business'
        }
        response = self.client.post(self.create_ticket_url, ticket_data)
        self.assertEqual(response.status_code, 200)
        
        # Check that the form is in the response context and has errors
        self.assertTrue('form' in response.context)
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('subject', form.errors)
        self.assertEqual(form.errors['subject'], ['This field is required.'])

    def test_ticket_detail_view(self):
        """Test viewing ticket details"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.ticket_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student/ticket_detail.html')
        self.assertEqual(response.context['ticket'], self.open_ticket)

    def test_add_message_to_ticket(self):
        """Test adding a message to a ticket"""
        self.client.login(username='testuser', password='testpass123')
        message_data = {
            'message': 'This is a test message'
        }
        response = self.client.post(self.ticket_detail_url, message_data)
        self.assertRedirects(response, self.ticket_detail_url)
        
        # Verify message was created
        self.assertTrue(Message.objects.filter(
            ticket=self.open_ticket,
            content='This is a test message'
        ).exists())

    def test_ticket_access_wrong_student(self):
        """Test that students cannot access other students' tickets"""
        # Create another student
        other_user = CustomUser.objects.create_user(
            username='otheruser',
            password='testpass123',
            email='other@example.com',
            first_name='Other',
            last_name='User',
            role='student'
        )
        other_student = Student.objects.create(
            user=other_user,
            department='business',
            program='Business Administration',
            year_of_study=2
        )
        
        # Create a ticket for the other student
        other_ticket = Ticket.objects.create(
            student=other_student,
            subject='Other Student Ticket',
            description='This is another student\'s ticket',
            department='business',
            status='open'
        )
        
        # Try to access the other student's ticket
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('ticket_detail', args=[other_ticket.id]))
        self.assertEqual(response.status_code, 404)

    def test_student_settings_view(self):
        """Test viewing student settings"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('student_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student/settings.html')
        self.assertEqual(response.context['name'], 'Test User')
        self.assertEqual(response.context['department'], 'business')
        self.assertEqual(response.context['program'], 'Business Administration')
        self.assertEqual(response.context['year_of_study'], 2)

    def test_create_ticket_with_long_subject(self):
        """Test ticket creation with subject exceeding max length"""
        self.client.login(username='testuser', password='testpass123')
        ticket_data = {
            'subject': 'x' * 201,  # Subject max length is 200
            'description': 'Test description',
            'department': 'business'
        }
        response = self.client.post(self.create_ticket_url, ticket_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertIn('subject', response.context['form'].errors)

    def test_create_ticket_with_empty_description(self):
        """Test ticket creation with empty description"""
        self.client.login(username='testuser', password='testpass123')
        ticket_data = {
            'subject': 'Test Subject',
            'description': '',
            'department': 'business'
        }
        response = self.client.post(self.create_ticket_url, ticket_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('description', response.context['form'].errors)

    def test_add_message_to_closed_ticket(self):
        """Test attempting to add a message to a closed ticket"""
        self.client.login(username='testuser', password='testpass123')
        closed_ticket_url = reverse('ticket_detail', args=[self.closed_ticket.id])
        response = self.client.post(closed_ticket_url, {'message': 'Test message'})
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('closed' in str(m).lower() for m in messages))

    def test_create_ticket_with_invalid_department(self):
        """Test ticket creation with invalid department"""
        self.client.login(username='testuser', password='testpass123')
        ticket_data = {
            'subject': 'Test Subject',
            'description': 'Test description',
            'department': 'invalid_department'
        }
        response = self.client.post(self.create_ticket_url, ticket_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('department', response.context['form'].errors)

    def test_add_empty_message(self):
        """Test adding an empty message to a ticket"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.ticket_detail_url, {'message': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.filter(ticket=self.open_ticket).count(), 0)

    def test_access_nonexistent_ticket(self):
        """Test accessing a ticket that doesn't exist"""
        self.client.login(username='testuser', password='testpass123')
        nonexistent_ticket_url = reverse('ticket_detail', args=[99999])
        response = self.client.get(nonexistent_ticket_url)
        self.assertEqual(response.status_code, 404)

    def test_create_multiple_tickets_same_subject(self):
        """Test creating multiple tickets with the same subject"""
        self.client.login(username='testuser', password='testpass123')
        ticket_data = {
            'subject': 'Duplicate Subject',
            'description': 'Test description',
            'department': 'business'
        }
        # Create first ticket
        response1 = self.client.post(self.create_ticket_url, ticket_data)
        self.assertEqual(response1.status_code, 302)
        # Create second ticket with same subject
        response2 = self.client.post(self.create_ticket_url, ticket_data)
        self.assertEqual(response2.status_code, 302)
        # Verify both tickets were created
        self.assertEqual(
            Ticket.objects.filter(subject='Duplicate Subject').count(),
            2
        )

    def test_staff_access_student_dashboard(self):
        """Test staff attempting to access student dashboard"""
        # Create staff user
        staff_user = CustomUser.objects.create_user(
            username='staffuser',
            password='staffpass123',
            email='staff@example.com',
            first_name='Staff',
            last_name='User',
            role='staff'
        )
        Staff.objects.create(user=staff_user, department='business', role='Staff Member')
        
        # Try to access student dashboard as staff
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)  # Should redirect to home

    def test_create_ticket_special_characters(self):
        """Test creating a ticket with special characters in subject and description"""
        self.client.login(username='testuser', password='testpass123')
        ticket_data = {
            'subject': '!@#$%^&*()',
            'description': '¡™£¢∞§¶•ªº',
            'department': 'business'
        }
        response = self.client.post(self.create_ticket_url, ticket_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ticket.objects.filter(subject='!@#$%^&*()').exists())

    def test_student_settings_dynamic_data(self):
        """Test that student settings page shows correct dynamic data"""
        self.client.login(username='testuser', password='testpass123')
        
        # Set a specific last login time
        self.user.last_login = timezone.now() - timedelta(days=1)
        self.user.save()
        
        response = self.client.get(reverse('student_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['account_type'], 'Student')
        self.assertEqual(response.context['status'], 'Active')
        self.assertIn(self.user.date_joined.strftime('%B'), response.context['member_since'])
        self.assertNotIn('Today at', response.context['last_login'])  # Should show date format since login was yesterday

    def test_dashboard_ticket_counts(self):
        """Test that dashboard shows correct ticket counts"""
        self.client.login(username='testuser', password='testpass123')
        
        # Clean up existing tickets and create fresh test data
        Ticket.objects.all().delete()
        
        # Create test tickets with specific statuses
        open_ticket1 = Ticket.objects.create(
            student=self.student,
            subject='First Open Ticket',
            description='This is the first open ticket',
            department='business',
            status='open'
        )
        
        open_ticket2 = Ticket.objects.create(
            student=self.student,
            subject='Second Open Ticket',
            description='This is the second open ticket',
            department='business',
            status='open'
        )
        
        pending_ticket = Ticket.objects.create(
            student=self.student,
            subject='Pending Ticket',
            description='This is a pending ticket',
            department='business',
            status='pending'
        )
        
        closed_ticket = Ticket.objects.create(
            student=self.student,
            subject='Closed Ticket',
            description='This is a closed ticket',
            department='business',
            status='closed',
            date_closed=timezone.now()
        )
        
        # Debug: Print all tickets
        print("\nAll tickets before test:")
        for ticket in Ticket.objects.all().order_by('subject'):
            print(f"- {ticket.subject} (Status: {ticket.status})")
        
        response = self.client.get(reverse('student_dashboard'))
        
        # Debug: Print tickets from response context
        print("\nTickets in response context:")
        print(f"Open tickets: {len(response.context['open_tickets'])}")
        for ticket in response.context['open_tickets'].order_by('subject'):
            print(f"- {ticket.subject} (Status: {ticket.status})")
        
        # Verify ticket counts
        self.assertEqual(len(response.context['open_tickets']), 2)  # Two open tickets
        self.assertEqual(len(response.context['closed_tickets']), 1)  # One closed ticket
        self.assertEqual(len(response.context['pending_tickets']), 1)  # One pending ticket
        
        # Verify specific tickets are in the correct lists
        open_tickets = list(response.context['open_tickets'].order_by('subject'))
        self.assertEqual(open_tickets[0].subject, 'First Open Ticket')
        self.assertEqual(open_tickets[1].subject, 'Second Open Ticket')
        
        pending_tickets = list(response.context['pending_tickets'])
        self.assertEqual(pending_tickets[0].subject, 'Pending Ticket')
        
        closed_tickets = list(response.context['closed_tickets'])
        self.assertEqual(closed_tickets[0].subject, 'Closed Ticket')

    def test_dashboard_empty_state(self):
        """Test dashboard display when student has no tickets"""
        # Create new student with no tickets
        new_user = CustomUser.objects.create_user(
            username='newstudent',
            password='testpass123',
            email='new@example.com',
            first_name='New',
            last_name='Student',
            role='student'
        )
        Student.objects.create(
            user=new_user,
            department='business',
            program='Business Administration',
            year_of_study=1
        )
        
        self.client.login(username='newstudent', password='testpass123')
        response = self.client.get(reverse('student_dashboard'))
        
        self.assertEqual(len(response.context['open_tickets']), 0)
        self.assertEqual(len(response.context['closed_tickets']), 0)
        self.assertContains(response, 'No open tickets found')
        self.assertContains(response, 'No past tickets found')

    def test_dashboard_ticket_ordering(self):
        """Test that tickets are displayed in correct order"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create tickets with specific dates
        older_ticket = Ticket.objects.create(
            student=self.student,
            subject='Older Ticket',
            description='This is an older ticket',
            department='business',
            status='open'
        )
        older_ticket.date_submitted = timezone.now() - timedelta(days=5)
        older_ticket.save()
        
        newer_ticket = Ticket.objects.create(
            student=self.student,
            subject='Newer Ticket',
            description='This is a newer ticket',
            department='business',
            status='open'
        )
        
        response = self.client.get(reverse('student_dashboard'))
        open_tickets = response.context['open_tickets']
        self.assertEqual(open_tickets[0], newer_ticket)  # Newest should be first
        self.assertEqual(open_tickets[2], older_ticket)  # Oldest should be last

    def test_dashboard_preferred_name_display(self):
        """Test that dashboard uses preferred name when available"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with no preferred name
        response = self.client.get(reverse('student_dashboard'))
        self.assertContains(response, self.user.first_name)
        
        # Test with preferred name
        self.user.preferred_name = 'Preferred'
        self.user.save()
        response = self.client.get(reverse('student_dashboard'))
        self.assertContains(response, 'Preferred')
        self.assertNotContains(response, self.user.first_name)

    def test_dashboard_access_after_password_change(self):
        """Test dashboard access after password change"""
        self.client.login(username='testuser', password='testpass123')
        
        # Change password
        self.user.set_password('newpassword123')
        self.user.save()
        
        # Should be logged out after password change
        response = self.client.get(reverse('student_dashboard'))
        self.assertRedirects(response, f'/login/?next={reverse("student_dashboard")}')
        
        # Should be able to log in with new password
        self.client.login(username='testuser', password='newpassword123')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_ticket_status_badges(self):
        """Test that ticket status badges show correct colors"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create tickets with different statuses
        pending_ticket = Ticket.objects.create(
            student=self.student,
            subject='Pending Ticket',
            description='This is a pending ticket',
            department='business',
            status='pending'
        )
        
        response = self.client.get(reverse('student_dashboard'))
        self.assertContains(response, 'bg-danger')  # Open ticket badge
        self.assertContains(response, 'bg-warning')  # Pending ticket badge
        self.assertContains(response, 'bg-secondary')  # Closed ticket badge

    def test_concurrent_ticket_creation(self):
        """Test handling of concurrent ticket creation"""
        self.client.login(username='testuser', password='testpass123')
        
        # Simulate concurrent ticket creation
        ticket_data = {
            'subject': 'Concurrent Ticket',
            'description': 'This is a concurrent ticket',
            'department': 'business'
        }
        
        # Create tickets almost simultaneously
        response1 = self.client.post(reverse('create_ticket'), ticket_data)
        response2 = self.client.post(reverse('create_ticket'), ticket_data)
        
        # Both tickets should be created successfully
        self.assertEqual(
            Ticket.objects.filter(subject='Concurrent Ticket').count(),
            2
        )
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response2.status_code, 302) 