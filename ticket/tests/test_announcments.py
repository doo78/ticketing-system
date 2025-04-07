from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from ticket.models import Student, Ticket, Announcement, Staff, AdminMessage, StudentMessage, CustomUser, Department

User = get_user_model()

class AdminViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.business_dept = Department.objects.create(name='Business')
        self.it_dept = Department.objects.create(name='IT')
        # Create admin user
        self.admin_user = CustomUser.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='adminpass',
            role='admin',
            first_name='Admin',
            last_name='User'
        )
        self.client.login(username='admin_user', password='adminpass')

        # Create staff user
        self.staff_user = CustomUser.objects.create_user(
            username='staff_user',
            email='staff@example.com',
            password='staffpass',
            role='staff',
            first_name='Staff',
            last_name='User'
        )
        self.staff = Staff.objects.create(
            user=self.staff_user,
            department=self.business_dept,
            role='IT Support'
        )

        # Create student user
        self.student_user = CustomUser.objects.create_user(
            username='student_user',
            email='student@example.com',
            password='studentpass',
            role='student',
            first_name='Student',
            last_name='User'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            department=self.business_dept,
            program='MBA',
            year_of_study=2
        )

        # Create ticket (with subject instead of title)
        self.ticket = Ticket.objects.create(
            subject='Wi-Fi Issue',
            description='Can’t connect to university Wi-Fi.',
            department=self.business_dept,
            status='open',
            student=self.student
        )

        # Create an announcement
        self.announcement = Announcement.objects.create(
            content='Test Announcement for Business',
            created_by=self.admin_user,
            department=self.business_dept,
        )

    def test_admin_ticket_detail_view(self):
        response = self.client.get(reverse('admin_ticket_detail', args=[self.ticket.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ticket.subject)

    def test_create_admin_message(self):
        response = self.client.post(reverse('admin_ticket_detail', args=[self.ticket.id]), {
            'message': 'This is a response from admin.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AdminMessage.objects.filter(ticket=self.ticket, content='This is a response from admin.').exists())

    def test_update_ticket_assign_staff(self):
        response = self.client.post(reverse('admin_ticket_detail', args=[self.ticket.id]), {
            'update_ticket': True,
            'department': str(self.it_dept.id),
            'status': 'in_progress',
            'assigned_staff': str(self.staff_user.id)
        })
        self.assertEqual(response.status_code, 302)
        updated_ticket = Ticket.objects.get(id=self.ticket.id)
        self.assertEqual(updated_ticket.assigned_staff, self.staff)

    def test_admin_announcements_page(self):
        response = self.client.get(reverse('admin_announcements'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Announcement')

    def test_create_announcement(self):
        self.admin_user = CustomUser.objects.create_user(
            username='admin2_user',
            email='admin2@example.com',
            password='adminpass',
            role='admin',
            first_name='Admin',
            last_name='User'
        )
        self.client.login(username='admin2_user', password='adminpass')
        response = self.client.post(reverse('create_announcement'), {
            'content': 'New test announcement',
            'department': ''
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Announcement.objects.filter(content='New test announcement').exists())

    def test_delete_announcement(self):
        response = self.client.post(reverse('delete_announcement', args=[self.announcement.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Announcement.objects.filter(id=self.announcement.id).exists())