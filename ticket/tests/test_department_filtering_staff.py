from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from ticket.models import Staff, Student, Ticket, CustomUser
from bs4 import BeautifulSoup

User = get_user_model()


class StaffTicketFilteringTests(TestCase):
    """Tests for the staff ticket filtering functionality."""

    def setUp(self):
        """Set up test data for filtering tests."""
        # Create staff users with different departments
        self.business_staff = self._create_staff_user('businessstaff', 'business')
        self.law_staff = self._create_staff_user('lawstaff', 'law')

        # Create student user
        self.student = self._create_student_user('student')

        # Create tickets in different departments with different statuses
        self.business_open_ticket = self._create_ticket('Business Query 1', 'business', 'open')
        self.business_pending_ticket = self._create_ticket('Business Query 2', 'business', 'pending')
        self.business_closed_ticket = self._create_ticket('Business Query 3', 'business', 'closed')

        self.law_open_ticket = self._create_ticket('Law Query 1', 'law', 'open')
        self.law_pending_ticket = self._create_ticket('Law Query 2', 'law', 'pending')
        self.law_closed_ticket = self._create_ticket('Law Query 3', 'law', 'closed')

        # Assign some tickets to staff
        self.business_pending_ticket.assigned_staff = self.business_staff
        self.business_pending_ticket.save()

        self.law_pending_ticket.assigned_staff = self.law_staff
        self.law_pending_ticket.save()

        # Create a client for making requests
        self.client = Client()

    def _create_staff_user(self, username, department):
        """Helper method to create a staff user with given department."""
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='testpassword',
            first_name='Test',
            last_name='Staff',
            role='staff'
        )
        staff = Staff.objects.create(
            user=user,
            department=department,
            role='Staff Member'
        )
        return staff

    def _create_student_user(self, username):
        """Helper method to create a student user."""
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='testpassword',
            first_name='Test',
            last_name='Student',
            role='student'
        )
        student = Student.objects.create(
            user=user,
            department='business',
            program='Business Admin',
            year_of_study=2
        )
        return student

    def _create_ticket(self, subject, department, status):
        """Helper method to create a ticket with given properties."""
        ticket = Ticket.objects.create(
            subject=subject,
            description=f'Test description for {subject}',
            department=department,
            student=self.student,
            status=status,
            date_submitted=timezone.now()
        )
        if status == 'closed':
            ticket.date_closed = timezone.now()

        return ticket

    def _login_staff(self, staff):
        """Helper method to log in as a staff member."""
        self.client.login(username=staff.user.username, password='testpassword')

    def test_all_tickets_view(self):
        """Test that staff can see all tickets when no filters are applied."""
        self._login_staff(self.business_staff)
        response = self.client.get(reverse('staff_ticket_list'))

        self.assertEqual(response.status_code, 200)

        # Check that all 6 tickets are visible
        self.assertContains(response, 'Business Query 1')
        self.assertContains(response, 'Business Query 2')
        self.assertContains(response, 'Business Query 3')
        self.assertContains(response, 'Law Query 1')
        self.assertContains(response, 'Law Query 2')
        self.assertContains(response, 'Law Query 3')

    def test_department_filter_business(self):
        """Test filtering tickets by the business department."""
        self._login_staff(self.business_staff)
        response = self.client.get(reverse('staff_ticket_list') + '?department_filter=mine')

        self.assertEqual(response.status_code, 200)

        # Should contain business tickets
        self.assertContains(response, 'Business Query 1')
        self.assertContains(response, 'Business Query 2')
        self.assertContains(response, 'Business Query 3')

        # Should not contain law tickets
        self.assertNotContains(response, 'Law Query 1')
        self.assertNotContains(response, 'Law Query 2')
        self.assertNotContains(response, 'Law Query 3')

    def test_department_filter_law(self):
        """Test filtering tickets by the law department."""
        self._login_staff(self.law_staff)
        response = self.client.get(reverse('staff_ticket_list') + '?department_filter=mine')

        self.assertEqual(response.status_code, 200)

        # Should not contain business tickets
        self.assertNotContains(response, 'Business Query 1')
        self.assertNotContains(response, 'Business Query 2')
        self.assertNotContains(response, 'Business Query 3')

        # Should contain law tickets
        self.assertContains(response, 'Law Query 1')
        self.assertContains(response, 'Law Query 2')
        self.assertContains(response, 'Law Query 3')

    def test_status_filter_open(self):
        """Test filtering tickets by open status."""
        self._login_staff(self.business_staff)
        response = self.client.get(reverse('staff_ticket_list') + '?status=open')

        self.assertEqual(response.status_code, 200)

        # Should contain open tickets
        self.assertContains(response, 'Business Query 1')
        self.assertContains(response, 'Law Query 1')

        # Should not contain pending or closed tickets
        self.assertNotContains(response, 'Business Query 2')
        self.assertNotContains(response, 'Business Query 3')
        self.assertNotContains(response, 'Law Query 2')
        self.assertNotContains(response, 'Law Query 3')

    def test_status_filter_pending(self):
        """Test filtering tickets by pending status."""
        self._login_staff(self.business_staff)
        response = self.client.get(reverse('staff_ticket_list') + '?status=pending')

        self.assertEqual(response.status_code, 200)

        # Should contain pending tickets
        self.assertContains(response, 'Business Query 2')
        self.assertContains(response, 'Law Query 2')

        # Should not contain open or closed tickets
        self.assertNotContains(response, 'Business Query 1')
        self.assertNotContains(response, 'Business Query 3')
        self.assertNotContains(response, 'Law Query 1')
        self.assertNotContains(response, 'Law Query 3')

    def test_status_filter_closed(self):
        """Test filtering tickets by closed status."""
        self._login_staff(self.business_staff)
        response = self.client.get(reverse('staff_ticket_list') + '?status=closed')

        self.assertEqual(response.status_code, 200)

        # Should contain closed tickets
        self.assertContains(response, 'Business Query 3')
        self.assertContains(response, 'Law Query 3')

        # Should not contain open or pending tickets
        self.assertNotContains(response, 'Business Query 1')
        self.assertNotContains(response, 'Business Query 2')
        self.assertNotContains(response, 'Law Query 1')
        self.assertNotContains(response, 'Law Query 2')

    def test_combined_filters_business_open(self):
        """Test combining department and status filters."""
        self._login_staff(self.business_staff)
        response = self.client.get(reverse('staff_ticket_list') + '?department_filter=mine&status=open')

        self.assertEqual(response.status_code, 200)

        # Should only contain business open tickets
        self.assertContains(response, 'Business Query 1')

        # Should not contain any other tickets
        self.assertNotContains(response, 'Business Query 2')
        self.assertNotContains(response, 'Business Query 3')
        self.assertNotContains(response, 'Law Query 1')
        self.assertNotContains(response, 'Law Query 2')
        self.assertNotContains(response, 'Law Query 3')

    def test_assign_ticket_preserves_filters(self):
        """Test that assigning a ticket preserves the current filter state."""
        self._login_staff(self.business_staff)

        # Start with the open tickets filter
        response = self.client.get(reverse('staff_ticket_list') + '?status=open')

        # Get the CSRF token for the form submission
        soup = BeautifulSoup(response.content, 'html.parser')
        csrf_token = soup.select('input[name="csrfmiddlewaretoken"]')[0]['value']

        # Submit the form to assign the open business ticket
        form_data = {
            'csrfmiddlewaretoken': csrf_token,
            'action': 'assign',
            'status_filter': 'open',
            'department_filter': 'all'
        }

        response = self.client.post(
            reverse('manage_ticket', kwargs={'ticket_id': self.business_open_ticket.id}),
            data=form_data,
            follow=True
        )

        # Should be redirected back to the open tickets filter
        self.assertEqual(response.status_code, 200)
        self.assertIn('?status=open', response.redirect_chain[0][0])

        # Ticket should now be assigned and pending
        updated_ticket = Ticket.objects.get(id=self.business_open_ticket.id)
        self.assertEqual(updated_ticket.status, 'pending')
        self.assertEqual(updated_ticket.assigned_staff, self.business_staff)

    def test_automatic_ticket_assignment(self):
        """Test that tickets are automatically assigned to staff in the matching department."""
        # Create a new ticket via the ticket creation form
        self._login_staff(self.business_staff)  # First login as staff to ensure auth middleware passes
        self.client.logout()  # Then logout to login as student

        self.client.login(username=self.student.user.username, password='testpassword')

        # Create a new business ticket
        response = self.client.post(
            reverse('create_ticket'),
            data={
                'subject': 'New Business Query',
                'description': 'This is a test query for business department',
                'department': 'business'
            },
            follow=True
        )

        # Check that the ticket was created and assigned to business staff
        new_ticket = Ticket.objects.get(subject='New Business Query')
        self.assertEqual(new_ticket.department, 'business')
        self.assertEqual(new_ticket.status, 'pending')  # Should be pending since it was assigned
        self.assertEqual(new_ticket.assigned_staff, self.business_staff)

        # Create a new law ticket
        response = self.client.post(
            reverse('create_ticket'),
            data={
                'subject': 'New Law Query',
                'description': 'This is a test query for law department',
                'department': 'law'
            },
            follow=True
        )

        # Check that the ticket was created and assigned to law staff
        new_ticket = Ticket.objects.get(subject='New Law Query')
        self.assertEqual(new_ticket.department, 'law')
        self.assertEqual(new_ticket.status, 'pending')  # Should be pending since it was assigned
        self.assertEqual(new_ticket.assigned_staff, self.law_staff)

    def test_unassigned_department_tickets_count(self):
        """Test that the staff dashboard shows the correct count of unassigned department tickets."""
        self._login_staff(self.business_staff)
        response = self.client.get(reverse('staff_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Department Tickets')

        # There should be 1 unassigned open business ticket
        self.assertContains(response, '1 unassigned')

    def test_filter_buttons_present(self):
        """Test that the filter buttons are present in the staff ticket list view."""
        self._login_staff(self.business_staff)
        response = self.client.get(reverse('staff_ticket_list'))

        self.assertEqual(response.status_code, 200)

        # Check for status filter buttons
        self.assertContains(response, 'All')
        self.assertContains(response, 'Open')
        self.assertContains(response, 'Pending')
        self.assertContains(response, 'Closed')

        # Check for department filter buttons
        self.assertContains(response, 'All Departments')
        self.assertContains(response, 'My Department')
        self.assertContains(response, 'Assigned To Me')
        
    def test_assigned_to_me_filter(self):
        """Test filtering tickets by the 'Assigned to Me' filter."""  
        self._login_staff(self.business_staff)  

        response = self.client.get(reverse('staff_ticket_list') + '?department_filter=assigned')

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Business Query 2') 
        self.assertNotContains(response, 'Business Query 1')  
        self.assertNotContains(response, 'Business Query 3') 
        self.assertNotContains(response, 'Law Query 1') 
        self.assertNotContains(response, 'Law Query 2')  
        self.assertNotContains(response, 'Law Query 3')