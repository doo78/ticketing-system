from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from ticket.models import CustomUser, Staff, Student, Ticket


class UnseedCommandTest(TestCase):
    """Test the unseed management command"""

    def setUp(self):
        # Create test users and data
        # Admin user
        admin_user = CustomUser.objects.create(
            username='admin_test',
            email='admin_test@example.com',
            first_name='Admin',
            last_name='Test',
            role='admin'
        )
        
        # Staff user with profile
        staff_user = CustomUser.objects.create(
            username='staff_test',
            email='staff_test@example.com',
            first_name='Staff',
            last_name='Test',
            role='staff'
        )
        staff = Staff.objects.create(user=staff_user, department='business', role='Support Staff')
        
        # Student user with profile
        student_user = CustomUser.objects.create(
            username='student_test',
            email='student_test@example.com',
            first_name='Student',
            last_name='Test',
            role='student'
        )
        student = Student.objects.create(
            user=student_user,
            department='business',
            program='Computer Science',
            year_of_study=2
        )
        
        # Create a superuser (should not be deleted)
        superuser = CustomUser.objects.create(
            username='superuser',
            email='super@example.com',
            first_name='Super',
            last_name='User',
            role='admin',
            is_superuser=True
        )
        
        # Create tickets
        Ticket.objects.create(
            subject='Test Ticket 1',
            description='This is a test ticket',
            student=student,
            assigned_staff=staff,
            status='pending',
            department='business'
        )
        
        Ticket.objects.create(
            subject='Test Ticket 2',
            description='This is another test ticket',
            student=student,
            status='open',
            department='business'
        )

    def test_unseed_command(self):
        """Test that the unseed command removes seeded data but leaves superusers"""
        # Verify initial state
        self.assertEqual(CustomUser.objects.count(), 4)  # 3 regular users + 1 superuser
        self.assertEqual(Staff.objects.count(), 1)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 2)
        
        # Run the unseed command
        out = StringIO()
        call_command('unseed', stdout=out)
        
        # Check that all tickets are deleted
        self.assertEqual(Ticket.objects.count(), 0)
        self.assertIn('All tickets deleted', out.getvalue())
        
        # Check that all staff and students are deleted
        self.assertEqual(Staff.objects.count(), 0)
        self.assertEqual(Student.objects.count(), 0)
        self.assertIn('All staff and students deleted', out.getvalue())
        
        # Check that regular users are deleted but superuser remains
        self.assertEqual(CustomUser.objects.count(), 1)  # Only the superuser should remain
        self.assertEqual(CustomUser.objects.filter(is_superuser=True).count(), 1)
        self.assertEqual(CustomUser.objects.filter(is_superuser=False).count(), 0)
        self.assertIn('All non-superuser users deleted', out.getvalue())
        
        # Check completion message
        self.assertIn('Database cleanup complete', out.getvalue())
    
    def test_unseed_command_with_empty_database(self):
        """Test that the unseed command works even if the database is already empty"""
        # First clear the database
        Ticket.objects.all().delete()
        Staff.objects.all().delete()
        Student.objects.all().delete()
        CustomUser.objects.all().delete()
        
        # Verify empty state
        self.assertEqual(CustomUser.objects.count(), 0)
        self.assertEqual(Staff.objects.count(), 0)
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)
        
        # Run the unseed command
        out = StringIO()
        call_command('unseed', stdout=out)
        
        # Check that it runs without errors
        self.assertIn('All tickets deleted', out.getvalue())
        self.assertIn('All staff and students deleted', out.getvalue())
        self.assertIn('All non-superuser users deleted', out.getvalue())
        self.assertIn('Database cleanup complete', out.getvalue()) 