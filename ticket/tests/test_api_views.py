from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ticket.models import Ticket, Staff, Student, CustomUser, Department
import json

User = get_user_model()

class AdminAPITestCase(TestCase):
    """Test cases for admin API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.business_dept = Department.objects.create(name='Business')
        self.eng_dept = Department.objects.create(name='Engineering')
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
            role='staff',
            first_name='Staff',
            last_name='Test'
        )
        self.staff = Staff.objects.create(user=self.staff_user, department=self.business_dept)
        
        # Create student user
        self.student_user = User.objects.create_user(
            username='studentuser',
            email='student@example.com',
            password='studentpass123',
            role='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            department=self.business_dept,
            program='Computer Science',
            year_of_study=2
        )
        
        # Create tickets
        self.open_ticket = Ticket.objects.create(
            subject='Open Ticket',
            description='This is an open ticket',
            status='open',
            student=self.student,
            department=self.business_dept
        )
        
        # URLs
        self.ticket_details_url = reverse('api_ticket')
        self.staff_by_department_url = reverse('api_get_staff_by_deparment')
        self.ticket_assign_url = reverse('ticket_assign')
        
        # Client
        self.client = Client()
        self.client.login(username='adminuser', password='adminpass123')

    def test_ticket_details_api(self):
        """Test admin API for ticket details"""
        data = {
            'ticket_id': self.open_ticket.id
        }
        
        response = self.client.post(
            self.ticket_details_url,
            json.dumps(data),
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse JSON response
        response_data = json.loads(response.content)
        
        # Check success flag
        self.assertTrue(response_data['success'])
        
        # Check ticket data
        ticket_data = response_data['response']
        self.assertEqual(ticket_data['ticket_id'], self.open_ticket.id)
        self.assertEqual(ticket_data['subject'], 'Open Ticket')
        self.assertEqual(ticket_data['description'], 'This is an open ticket')
        self.assertEqual(ticket_data['status'], 'open')
    
    def test_ticket_details_api_invalid_id(self):
        """Test admin API for ticket details with invalid ID"""
        data = {
            'ticket_id': 9999  # Non-existent ticket ID
        }
        
        response = self.client.post(
            self.ticket_details_url,
            json.dumps(data),
            content_type='application/json'
        )
        
        # Check response status (should be 404)
        self.assertEqual(response.status_code, 404)
        
        # Parse JSON response
        response_data = json.loads(response.content)
        
        # Check error response
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Ticket not found')
    
    def test_ticket_details_api_missing_id(self):
        """Test admin API for ticket details with missing ID"""
        data = {}  # No ticket_id
        
        response = self.client.post(
            self.ticket_details_url,
            json.dumps(data),
            content_type='application/json'
        )
        
        # Check response status (should be 400)
        self.assertEqual(response.status_code, 400)
        
        # Parse JSON response
        response_data = json.loads(response.content)
        
        # Check error response
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'ticket_id is required')
    
    def test_staff_by_department_api(self):
        """Test admin API for staff by department"""
        data = {
            'department': str(self.business_dept.id)
        }
        
        response = self.client.post(
            self.staff_by_department_url,
            json.dumps(data),
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse JSON response
        response_data = json.loads(response.content)
        
        # Check success flag
        self.assertTrue(response_data['success'])
        
        # Check staff data
        staff_list = response_data['response']
        self.assertEqual(len(staff_list), 1)
        self.assertEqual(staff_list[0]['id'], self.staff.id)
        self.assertEqual(staff_list[0]['name'], 'Staff Test')
    
    def test_staff_by_department_api_missing_department(self):
        """Test admin API for staff by department with missing department"""
        data = {}  # No department
        
        response = self.client.post(
            self.staff_by_department_url,
            json.dumps(data),
            content_type='application/json'
        )
        
        # Check response status (should be 400)
        self.assertEqual(response.status_code, 400)
        
        # Parse JSON response
        response_data = json.loads(response.content)
        
        # Check error response
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'department is required')
    
    def test_ticket_assign_api(self):
        """Test admin API for ticket assignment"""
        data = {
            'ticket_id': self.open_ticket.id,
            'assigned_staff_id': self.staff.id,
            'department': str(self.business_dept.id),
            'ticket_status': False
        }
        
        response = self.client.post(
            self.ticket_assign_url,
            json.dumps(data),
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse JSON response
        response_data = json.loads(response.content)
        
        # Check success flag
        self.assertTrue(response_data['success'])
        
        # Check ticket was updated
        self.open_ticket.refresh_from_db()
        self.assertEqual(self.open_ticket.assigned_staff_id, self.staff.id)
        self.assertEqual(self.open_ticket.department, self.business_dept)
        self.assertEqual(self.open_ticket.status, 'pending')
    
    def test_ticket_assign_api_department_only(self):
        """Test admin API for ticket assignment with department only"""
        data = {
            'ticket_id': self.open_ticket.id,
            'assigned_staff_id': '',
            'department': str(self.eng_dept.id),
            'ticket_status': False
        }
        
        response = self.client.post(
            self.ticket_assign_url,
            json.dumps(data),
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse JSON response
        response_data = json.loads(response.content)
        
        # Check success flag
        self.assertTrue(response_data['success'])
        
        # Check ticket was updated
        self.open_ticket.refresh_from_db()
        self.assertIsNone(self.open_ticket.assigned_staff)
        self.assertEqual(self.open_ticket.department, self.eng_dept)
        self.assertEqual(self.open_ticket.status, 'open') 