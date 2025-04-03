from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ticket.models import Ticket, Staff, Student, CustomUser
from ticket.views import AdminUpdateForm

User = get_user_model()

class AdminViewsTestCase(TestCase):
    """Test cases for admin views"""

    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            role='staff'
        )
        self.staff = Staff.objects.create(user=self.staff_user, department='business')
        
        # Create student user
        self.student_user = User.objects.create_user(
            username='studentuser',
            email='student@example.com',
            password='studentpass123',
            role='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            department='business',
            program='Computer Science',
            year_of_study=2
        )
        
        # Create tickets
        self.open_ticket = Ticket.objects.create(
            subject='Open Ticket',
            description='This is an open ticket',
            status='open',
            student=self.student
        )
        
        self.pending_ticket = Ticket.objects.create(
            subject='Pending Ticket',
            description='This is a pending ticket',
            status='pending',
            student=self.student,
            assigned_staff=self.staff
        )
        
        self.closed_ticket = Ticket.objects.create(
            subject='Closed Ticket',
            description='This is a closed ticket',
            status='closed',
            student=self.student,
            assigned_staff=self.staff
        )
        
        # URLs
        self.admin_dashboard_url = reverse('admin_dashboard')
        self.admin_ticket_list_url = reverse('admin_ticket_list')
        self.admin_account_url = reverse('admin_account')
        self.admin_accounts_list_url = reverse('admin_accounts_list')
        
        # Client
        self.client = Client()
        self.client.login(username='adminuser', password='adminpass123')

    def test_admin_dashboard(self):
        """Test admin dashboard view"""
        response = self.client.get(self.admin_dashboard_url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin-panel/admin_dashboard.html')
        
        # Check context data
        self.assertEqual(response.context['open_tickets_count'], 1)
        self.assertEqual(response.context['pending_tickets_count'], 1)
        self.assertEqual(response.context['closed_tickets_count'], 1)
        self.assertEqual(response.context['tickets_count'], 3)
        self.assertTrue('recent_activities' in response.context)
    
    def test_admin_ticket_list(self):
        """Test admin ticket list view"""
        response = self.client.get(self.admin_ticket_list_url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin-panel/admin_ticket_list.html')
        
        # Check context data
        self.assertEqual(len(response.context['tickets']), 3)
        self.assertEqual(response.context['open_count'], 1)
        self.assertEqual(response.context['pending_count'], 1)
        self.assertEqual(response.context['closed_count'], 1)
    
    def test_admin_ticket_list_with_filters(self):
        """Test admin ticket list view with status filter"""
        response = self.client.get(f"{self.admin_ticket_list_url}?status=open")
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Check filtered tickets
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].status, 'open')
    
    def test_admin_accounts_view_get(self):
        """Test admin account creation view GET"""
        response = self.client.get(self.admin_account_url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin-panel/admin_accounts.html')
        
        # Check form in context
        self.assertTrue('form' in response.context)
        self.assertFalse(response.context['is_update'])
    
    def test_admin_accounts_view_post_success(self):
        """Test admin account creation view POST success"""
        new_user_data = {
            'username': 'newuser',
            'password1': 'complex-password123',
            'password2': 'complex-password123',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'staff',
        }
        
        response = self.client.post(self.admin_account_url, new_user_data)
        
        # Check redirect
        self.assertRedirects(response, self.admin_accounts_list_url)
        
        # Check user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Check staff profile was created
        new_user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(new_user, 'staff'))
    
    def test_admin_accounts_list_view(self):
        """Test admin accounts list view"""
        response = self.client.get(self.admin_accounts_list_url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin-panel/admin_accounts_list.html')
        
        # Check context data
        self.assertEqual(response.context['admin_count'], 1)
        self.assertEqual(response.context['staff_count'], 1)
        self.assertEqual(response.context['student_count'], 1)
        self.assertEqual(len(response.context['accounts']), 3)
    
    def test_admin_accounts_list_with_filter(self):
        """Test admin accounts list view with role filter"""
        response = self.client.get(f"{self.admin_accounts_list_url}?account_type=staff")
        
        # Check filtered accounts
        self.assertEqual(len(response.context['accounts']), 1)
        self.assertEqual(response.context['accounts'][0].role, 'staff')
    
    def test_admin_accounts_delete(self):
        """Test deleting a user account"""
        account_id = self.student_user.id
        response = self.client.post(self.admin_accounts_list_url, {'account_id': account_id})
        
        # Check redirect
        self.assertRedirects(response, self.admin_accounts_list_url)
        
        # Check user was deleted
        self.assertFalse(User.objects.filter(id=account_id).exists()) 
    from django.urls import reverse

    def test_admin_update_profile_get(self):
        self.client.login(username='admin_user', password='adminpass')
        response = self.client.get(reverse('admin_update_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], AdminUpdateForm)
        self.assertContains(response, 'Update')  

    def test_admin_update_profile_post_valid(self):
        self.client.login(username='admin_user', password='adminpass')
        response = self.client.post(reverse('admin_update_profile'), {
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'newadmin@example.com',
            'username': 'admin_user'
        })
        self.assertRedirects(response, reverse('admin_profile'))
        
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.first_name, 'Updated')
        self.assertEqual(self.admin_user.email, 'newadmin@example.com')

    def test_admin_update_profile_redirect_if_not_admin(self):
        self.client.login(username='studentuser', password='studentpass')
        response = self.client.get(reverse('admin_update_profile'))
        self.assertRedirects(response, reverse('admin_dashboard'))    