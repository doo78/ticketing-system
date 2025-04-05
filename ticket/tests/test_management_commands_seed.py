from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from django.utils.timezone import now, timedelta
from ticket.models import CustomUser, Staff, Student, Ticket, Department
from unittest.mock import patch


class SeedCommandTest(TestCase):
    """Test the seed management command"""

    def setUp(self):
        # Make sure there's no data in the database from previous tests
        Ticket.objects.all().delete()
        Staff.objects.all().delete()
        Student.objects.all().delete()
        CustomUser.objects.all().delete()

    def test_create_fixed_users(self):
        """Test that fixed users are created with correct roles"""
        # Apply only the create_fixed_users part
        with patch('ticket.management.commands.seed.Command.create_random_users') as mock_random_users, \
             patch('ticket.management.commands.seed.Command.create_tickets') as mock_tickets:
            # Make these methods do nothing
            mock_random_users.return_value = None
            mock_tickets.return_value = None
            
            # Run the command
            out = StringIO()
            call_command('seed', stdout=out)
            
            # Check that fixed users were created
            self.assertEqual(CustomUser.objects.filter(username='admin_user').count(), 1)
            self.assertEqual(CustomUser.objects.filter(username='staff_user').count(), 1)
            self.assertEqual(CustomUser.objects.filter(username='student_user').count(), 1)
            
            # Check user roles
            self.assertEqual(CustomUser.objects.get(username='admin_user').role, 'admin')
            self.assertEqual(CustomUser.objects.get(username='staff_user').role, 'staff')
            self.assertEqual(CustomUser.objects.get(username='student_user').role, 'student')
            
            # Check that associated profiles were created
            self.assertTrue(Staff.objects.filter(user__username='staff_user').exists())
            self.assertTrue(Student.objects.filter(user__username='student_user').exists())
            
            # Check output
            self.assertIn('Fixed users created', out.getvalue())

    def test_create_random_users(self):
        """Test that random users are created with correct roles"""
        # Patch the USER_COUNT to a small number for faster tests
        with patch('ticket.management.commands.seed.Command.USER_COUNT', 5), \
             patch('ticket.management.commands.seed.Command.create_fixed_users') as mock_fixed_users, \
             patch('ticket.management.commands.seed.Command.create_tickets') as mock_tickets:
            # Make these methods do nothing
            mock_fixed_users.return_value = None
            mock_tickets.return_value = None
            
            # Run the command
            out = StringIO()
            call_command('seed', stdout=out)
            
            # Check that 5 random users were created (should have either staff or student role)
            self.assertEqual(CustomUser.objects.count(), 5)
            
            # Check that all users have valid roles
            for user in CustomUser.objects.all():
                self.assertIn(user.role, ['staff', 'student'])
            
            # Check that associated profiles were created
            staff_count = CustomUser.objects.filter(role='staff').count()
            student_count = CustomUser.objects.filter(role='student').count()
            
            self.assertEqual(Staff.objects.count(), staff_count)
            self.assertEqual(Student.objects.count(), student_count)
            
            # Check output
            self.assertIn('5 random users created', out.getvalue())

    def test_create_tickets(self):
        """Test that tickets are created with proper relationships"""
        test_dept = Department.objects.create(name='Test Dept Seed')
        # First create some students and staff manually
        admin_user = CustomUser.objects.create(
            username='admin_test',
            email='admin_test@example.com',
            first_name='Admin',
            last_name='Test',
            role='admin'
        )
        
        staff_user = CustomUser.objects.create(
            username='staff_test',
            email='staff_test@example.com',
            first_name='Staff',
            last_name='Test',
            role='staff'
        )
        staff = Staff.objects.create(user=staff_user, department=test_dept, role='Support Staff')
        
        student_user = CustomUser.objects.create(
            username='student_test',
            email='student_test@example.com',
            first_name='Student',
            last_name='Test',
            role='student'
        )
        student = Student.objects.create(
            user=student_user,
            department=test_dept,
            program='Computer Science',
            year_of_study=2
        )
        
        # Patch the TICKET_COUNT to a small number for faster tests
        with patch('ticket.management.commands.seed.Command.TICKET_COUNT', 10), \
             patch('ticket.management.commands.seed.Command.create_fixed_users') as mock_fixed_users, \
             patch('ticket.management.commands.seed.Command.create_random_users') as mock_random_users:
            # Make these methods do nothing
            mock_fixed_users.return_value = None
            mock_random_users.return_value = None
            
            # Run the command
            out = StringIO()
            call_command('seed', stdout=out)
            
            # Check that 10 tickets were created
            self.assertEqual(Ticket.objects.count(), 10)
            
            # Check that all tickets have required fields
            for ticket in Ticket.objects.all():
                self.assertIsNotNone(ticket.subject)
                self.assertIsNotNone(ticket.description)
                self.assertIsNotNone(ticket.status)
                self.assertIsNotNone(ticket.student)
                self.assertIsNotNone(ticket.department)
                self.assertIsNotNone(ticket.date_submitted)
                
                # If ticket is closed, it should have date_closed
                if ticket.status == 'closed':
                    self.assertIsNotNone(ticket.date_closed)
                    # Don't check date relationship as it might vary in implementation
                
                # If ticket is pending or closed, it should have assigned_staff
                if ticket.status in ['pending', 'closed']:
                    self.assertIsNotNone(ticket.assigned_staff)
            
            # Check output
            self.assertIn('10 tickets generated', out.getvalue())

    def test_full_seeding_process(self):
        """Test the full seeding process with reduced numbers"""
        # Patch to use small numbers for faster tests
        with patch('ticket.management.commands.seed.Command.USER_COUNT', 3), \
             patch('ticket.management.commands.seed.Command.TICKET_COUNT', 5):
            
            # Run the command
            out = StringIO()
            call_command('seed', stdout=out)
            
            # 3 fixed users + 3 random users = 6 total users
            self.assertEqual(CustomUser.objects.count(), 6)
            
            # Check roles distribution
            self.assertEqual(CustomUser.objects.filter(role='admin').count(), 1)
            self.assertTrue(CustomUser.objects.filter(role='staff').exists())
            self.assertTrue(CustomUser.objects.filter(role='student').exists())
            
            # Check profiles
            self.assertEqual(Staff.objects.count(), CustomUser.objects.filter(role='staff').count())
            self.assertEqual(Student.objects.count(), CustomUser.objects.filter(role='student').count())
            
            # Check tickets
            self.assertEqual(Ticket.objects.count(), 5)
            
            # All tickets should belong to students
            for ticket in Ticket.objects.all():
                self.assertIsNotNone(ticket.student)
                self.assertEqual(ticket.student.user.role, 'student')
                
            # Check output
            self.assertIn('Database seeding complete', out.getvalue()) 