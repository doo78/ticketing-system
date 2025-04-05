from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from ticket.models import Staff, Student, Ticket, CustomUser, Department

User = get_user_model()


class TicketAssignmentTests(TestCase):
    """Tests for the automatic ticket assignment functionality."""

    def setUp(self):
        """Set up test data for assignment tests."""
        self.business_dept = Department.objects.create(name='Business')
        self.law_dept = Department.objects.create(name='Law')
        self.arts_dept = Department.objects.create(name='Arts & Humanities')
        self.nursing_dept = Department.objects.create(name='Nursing')
        self.psych_dept = Department.objects.create(name='Psychiatry')
        # Create multiple staff users in the same department to test load balancing
        self.business_staff1 = self._create_staff_user('business_staff1', self.business_dept)
        self.business_staff2 = self._create_staff_user('business_staff2', self.business_dept)
        self.business_staff3 = self._create_staff_user('business_staff3', self.business_dept)

        # Create staff in different departments
        self.law_staff = self._create_staff_user('law_staff', self.law_dept)
        self.arts_staff = self._create_staff_user('arts_staff', self.arts_dept)

        # Create students
        self.business_student = self._create_student_user('business_student', self.business_dept)
        self.law_student = self._create_student_user('law_student', self.law_dept)

        # Assign some tickets to staff to test load balancing
        # business_staff1 has 3 active tickets
        for i in range(3):
            self._create_ticket(f'Business Staff 1 Ticket {i}', self.business_dept, 'pending',
                                self.business_student, self.business_staff1)
            self._create_ticket('Business Staff 2 Ticket', self.business_dept, 'pending',
                                self.business_student, self.business_staff2)
            self._create_ticket('Law Staff Ticket', self.law_dept, 'pending',
                                self.law_student, self.law_staff)

        # business_staff2 has 1 active ticket
        self._create_ticket('Business Staff 2 Ticket', self.business_dept, 'pending',
                            self.business_student, self.business_staff2)

        # business_staff3 has 0 active tickets
        # (no tickets created for this staff intentionally)

        # Create some existing tickets for law department
        self._create_ticket('Law Staff Ticket', self.law_dept, 'pending',
                            self.law_student, self.law_staff)

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

    def _create_student_user(self, username, department):
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
            department=department,
            program='Test Program',
            year_of_study=2
        )
        return student

    def _create_ticket(self, subject, department, status, student, assigned_staff=None):
        """Helper method to create a ticket with given properties."""
        ticket = Ticket.objects.create(
            subject=subject,
            description=f'Test description for {subject}',
            department=department,
            student=student,
            status=status,
            date_submitted=timezone.now(),
            assigned_staff=assigned_staff
        )
        if status == 'closed':
            ticket.date_closed = timezone.now()

        return ticket

    def test_load_balancing_assignment(self):
        """Test that new tickets are assigned to staff with fewest active tickets."""
        # Login as business student
        self.client.login(username=self.business_student.user.username, password='testpassword')

        # Create a new business ticket
        response = self.client.post(
            reverse('create_ticket'),
            data={
                'subject': 'New Business Query for Load Balancing',
                'description': 'This is a test query for load balancing',
                'department': str(self.business_dept.id)
            },
            follow=True
        )

        # The ticket should be assigned to business_staff3 (0 active tickets)
        new_ticket = Ticket.objects.get(subject='New Business Query for Load Balancing')
        self.assertEqual(new_ticket.assigned_staff, self.business_staff3)
        self.assertEqual(new_ticket.status, 'pending')

        # Create another business ticket
        response = self.client.post(
            reverse('create_ticket'),
            data={
                'subject': 'Second Business Query for Load Balancing',
                'description': 'This is another test query for load balancing',
                'department': str(self.business_dept.id)
            },
            follow=True
        )

        # At this point, staff2 and staff3 both have 1 ticket, so either could be chosen
        second_ticket = Ticket.objects.get(subject='Second Business Query for Load Balancing')
        self.assertIn(second_ticket.assigned_staff, [self.business_staff2, self.business_staff3])

        # Create two more tickets for staff3 to make it have more tickets than staff2
        for i in range(2):
            self._create_ticket(f'Extra Business Staff 3 Ticket {i}', self.business_dept, 'pending',
                                self.business_student, self.business_staff3)

        # Create another business ticket
        response = self.client.post(
            reverse('create_ticket'),
            data={
                'subject': 'Third Business Query for Load Balancing',
                'description': 'Yet another test query for load balancing',
                'department': str(self.business_dept.id)
            },
            follow=True
        )

        # Now the ticket should be assigned to business_staff2 (fewer active tickets)
        third_ticket = Ticket.objects.get(subject='Third Business Query for Load Balancing')
        self.assertEqual(third_ticket.assigned_staff, self.business_staff2)

    def test_department_specific_assignment(self):
        """Test that tickets are assigned to staff in the matching department."""
        # Login as law student
        self.client.login(username=self.law_student.user.username, password='testpassword')

        # Create a new law ticket
        response = self.client.post(
            reverse('create_ticket'),
            data={
                'subject': 'New Law Query',
                'description': 'This is a test query for law department',
                'department': str(self.law_dept.id)
            },
            follow=True
        )

        # The ticket should be assigned to law_staff
        new_ticket = Ticket.objects.get(subject='New Law Query')
        self.assertEqual(new_ticket.assigned_staff, self.law_staff)
        self.assertEqual(new_ticket.status, 'pending')

        # Create a ticket for a department with no staff
        response = self.client.post(
            reverse('create_ticket'),
            data={
                'subject': 'Query for Department with No Staff',
                'description': 'This is a test query for a department with no staff',
                'department': str(self.nursing_dept.id)  # No staff assigned to nursing
            },
            follow=True
        )

        # The ticket should be created but not assigned
        new_ticket = Ticket.objects.get(subject='Query for Department with No Staff')
        self.assertIsNone(new_ticket.assigned_staff)
        self.assertEqual(new_ticket.status, 'open')  # Should remain open since no staff assigned

    def test_student_notification_on_assignment(self):
        """Test that appropriate message is shown to student when ticket is assigned or not."""
        # Login as business student
        self.client.login(username=self.business_student.user.username, password='testpassword')

        # Create a ticket that should be assigned
        response = self.client.post(
            reverse('create_ticket'),
            data={
                'subject': 'Business Assignment Notification Test',
                'description': 'Testing assignment notification',
                'department': str(self.business_dept.id),
            },
            follow=True
        )

        # Check that the success message includes "assigned to a staff member"
        messages = list(response.context['messages'])
        self.assertTrue(any('assigned to a staff member' in str(message) for message in messages))

        # Create a ticket that can't be assigned (no staff for psychiatry)
        response = self.client.post(
            reverse('create_ticket'),
            data={
                'subject': 'Psychiatry Assignment Notification Test',
                'description': 'Testing unassigned notification',
                'department': str(self.psych_dept.id)  # Assuming no staff assigned to psychiatry
            },
            follow=True
        )

        # Check that the success message just says "submitted successfully"
        messages = list(response.context['messages'])
        self.assertTrue(any('submitted successfully' in str(message) and 'assigned' not in str(message)
                            for message in messages))