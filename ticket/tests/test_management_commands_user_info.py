from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from ticket.models import CustomUser


class UserInfoCommandTest(TestCase):
    """Test the user_info management command"""

    def setUp(self):
        # Create some test users
        self.admin_user = CustomUser.objects.create(
            username='admin_test',
            email='admin_test@example.com',
            first_name='Admin',
            last_name='Test',
            role='admin'
        )
        
        self.staff_user = CustomUser.objects.create(
            username='staff_test',
            email='staff_test@example.com',
            first_name='Staff',
            last_name='Test',
            role='staff'
        )
        
        self.student_user = CustomUser.objects.create(
            username='student_test',
            email='student_test@example.com',
            first_name='Student',
            last_name='Test',
            role='student'
        )

    def test_user_info_command_with_users(self):
        """Test that the user_info command displays information about all users"""
        # Run the command
        out = StringIO()
        call_command('user_info', stdout=out)
        output = out.getvalue()
        
        # Check that the command output contains the success message
        self.assertIn('Listing all users', output)
        
        # Check that each user is listed with their information
        self.assertIn('Username: admin_test', output)
        self.assertIn('Role: admin', output)
        
        self.assertIn('Username: staff_test', output)
        self.assertIn('Role: staff', output)
        
        self.assertIn('Username: student_test', output)
        self.assertIn('Role: student', output)
        
        # Check that the default password is shown
        self.assertIn('Password: password123', output)

    def test_user_info_command_with_no_users(self):
        """Test that the user_info command shows a warning when no users exist"""
        # First delete all users
        CustomUser.objects.all().delete()
        
        # Run the command
        out = StringIO()
        call_command('user_info', stdout=out)
        output = out.getvalue()
        
        # Check that the warning message is displayed
        self.assertIn('No users found in the database', output)
        
        # Make sure success message is not there
        self.assertNotIn('Listing all users', output)

    def test_user_info_command_format(self):
        """Test that the user_info command displays user information in the expected format"""
        # Create a user with specific values to check formatting
        test_user = CustomUser.objects.create(
            username='format_test',
            email='format@example.com',
            first_name='Format',
            last_name='Test',
            role='student'
        )
        
        # Run the command
        out = StringIO()
        call_command('user_info', stdout=out)
        output = out.getvalue()
        
        # Check for the specific user's information format
        expected_format = f"Username: format_test, Name : {'Format', 'Test'} Role: student, Password: password123"
        self.assertIn(expected_format, output) 