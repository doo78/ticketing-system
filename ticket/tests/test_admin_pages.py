from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ticket.models import Ticket, Staff, Student
from django.core.exceptions import PermissionDenied
from ticket.models import Announcement
from django.contrib.auth.models import Permission

class AdminDashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass", role="admin"
        )

        Ticket.objects.create(subject="Open Ticket", status="open")
        Ticket.objects.create(subject="Closed Ticket", status="closed")
        Ticket.objects.create(subject="Pending Ticket", status="pending")

    def test_dashboard_loads_for_admin(self):
        """Test that an authenticated admin can access the dashboard."""
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)  
        self.assertTemplateUsed(response, 'admin-panel/admin_dashboard.html')

class AdminTicketListViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_user = get_user_model().objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpass",
            role="admin",
        )

        self.ticket1 = Ticket.objects.create(subject="Ticket 1", status="open")
        self.ticket2 = Ticket.objects.create(subject="Ticket 2", status="closed")
        self.ticket3 = Ticket.objects.create(subject="Ticket 3", status="pending")

    def test_ticket_list_loads_for_admin(self):
        """Admin can access the ticket list page."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(reverse('admin_ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin-panel/admin_ticket_list.html')

    def test_ticket_list_filters_by_status(self):
        """Ensure filtering by ticket status works."""
        self.client.login(username="adminuser", password="adminpass")
        
        response = self.client.get(reverse('admin_ticket_list'), {'status': 'open'})
        self.assertEqual(response.context["tickets"].count(), 1)
        self.assertEqual(response.context["tickets"].first().status, "open")

        response = self.client.get(reverse('admin_ticket_list'), {'status': 'closed'})
        self.assertEqual(response.context["tickets"].count(), 1)
        self.assertEqual(response.context["tickets"].first().status, "closed")

    def test_ticket_list_sorting(self):
        """Ensure ordering works based on attributes."""
        self.client.login(username="adminuser", password="adminpass")

        response = self.client.get(reverse('admin_ticket_list'))
        tickets = list(response.context["tickets"])
        self.assertTrue(tickets[0].id < tickets[1].id)

        response = self.client.get(reverse('admin_ticket_list'), {'order': 'desc'})
        tickets = list(response.context["tickets"])
        self.assertTrue(tickets[0].id > tickets[1].id)
    

class AdminAccountEditViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_user = get_user_model().objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpass",
            role="admin",
        )

        self.staff_user = get_user_model().objects.create_user(
            username="staffuser",
            email="staffuser@example.com",
            password="staffpassword",
            role="staff",
        )

        self.student_user = get_user_model().objects.create_user(
            username="studentuser",
            email="studentuser@example.com",
            password="studentpassword",
            role="student",
        )

    def test_admin_account_edit_view_get(self):
        """Ensure the edit form is displayed correctly for editing a user's account."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(reverse('admin_edit_account', kwargs={'account_id': self.staff_user.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin-panel/admin_accounts.html')

    def test_admin_account_edit_view_post_edit_staff(self):
        """Test editing an existing staff account."""
        self.client.login(username="adminuser", password="adminpass")

        data = {
            'username': 'updatedstaffuser',
            'first_name': 'Updated',
            'last_name': 'Staff',
            'email': 'updatedstaffuser@example.com',
            'password1': 'newpassword',
            'password2': 'newpassword',
            'role': 'staff',
        }

        response = self.client.post(reverse('admin_edit_account', kwargs={'account_id': self.staff_user.id}), data)

        self.assertRedirects(response, reverse('admin_accounts_list'))

        updated_staff = get_user_model().objects.get(id=self.staff_user.id)
        self.assertEqual(updated_staff.username, 'updatedstaffuser')
        self.assertEqual(updated_staff.first_name, 'Updated')
        self.assertEqual(updated_staff.last_name, 'Staff')
        self.assertEqual(updated_staff.email, 'updatedstaffuser@example.com')

    def test_admin_account_edit_view_post_edit_student(self):
        """Test editing an existing student account."""
        self.client.login(username="adminuser", password="adminpass")

        data = {
            'username': 'updatedstudentuser',
            'first_name': 'Updated',
            'last_name': 'Student',
            'email': 'updatedstudentuser@example.com',
            'password1': 'newpassword',
            'password2': 'newpassword',
            'role': 'student',
            'department': 'business',
            'program': 'MBA',
            'year_of_study': 2,
        }

        response = self.client.post(reverse('admin_edit_account', kwargs={'account_id': self.student_user.id}), data)

        self.assertRedirects(response, reverse('admin_accounts_list'))

        updated_student = get_user_model().objects.get(id=self.student_user.id)

        student_profile, created = Student.objects.get_or_create(user=updated_student, defaults={
            "department": data["department"],
            "program": data["program"],
            "year_of_study": data["year_of_study"],
        })

        self.assertEqual(updated_student.username, 'updatedstudentuser')
        self.assertEqual(updated_student.first_name, 'Updated')
        self.assertEqual(updated_student.last_name, 'Student')
        self.assertEqual(updated_student.email, 'updatedstudentuser@example.com')

        self.assertEqual(student_profile.department, 'business')
        self.assertEqual(student_profile.program, 'MBA')
        self.assertEqual(student_profile.year_of_study, 2)

class CreateAnnouncementTest(TestCase):

    def setUp(self):
        """Set up users and test data."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="adminpass",
            role="admin"
        )
        self.staff_user = get_user_model().objects.create_superuser(
            username="staffuser",
            email="staff@example.com",
            password="staffpass",
            role="staff"
        )

        self.announcement_url = reverse('create_announcement')  

    def test_admin_can_create_announcement(self):
        """Admin should be able to create an announcement."""
                
        login_successful = self.client.login(username="adminuser", password="adminpass")
        
        response = self.client.post(self.announcement_url, {
            'content': 'Important Announcement',
            'department': 'business'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("admin_announcements"))

        self.assertTrue(Announcement.objects.filter(content="Important Announcement").exists())

    def test_non_admin_cannot_create_announcement(self):
        """Non-admin users should get PermissionDenied when trying to create an announcement."""
        self.client.login(username="staffuser", password="staffpass")

        response = self.client.post(self.announcement_url, {
            'content': 'Unauthorized Announcement',
            'department': 'business'
        })

        self.assertEqual(response.status_code, 403)  
        self.assertFalse(Announcement.objects.exists())
    
