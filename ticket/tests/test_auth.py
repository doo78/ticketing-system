from django.test import TestCase, Client
from django.urls import reverse
from ticket.models import CustomUser, Staff


class StaffAuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('sign_up')
        self.login_url = reverse('log_in')

    def test_staff_signup_success(self):
        response = self.client.post(self.signup_url, {
            'username': 'staffuser',
            'email': 'staff@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'staff'
        })
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(Staff.objects.count(), 1)
        self.assertRedirects(response, reverse('log_in'))

    def test_staff_login_success(self):
        user = CustomUser.objects.create_user(
            username='staffuser',
            password='testpass123',
            role='staff'
        )
        Staff.objects.create(user=user, department='', role='Staff Member')

        response = self.client.post(self.login_url, {
            'username': 'staffuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('staff_dashboard'))

    def test_staff_invalid_login(self):
        response = self.client.post(self.login_url, {
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_staff_signup_duplicate_email(self):
        CustomUser.objects.create_user(
            username='existinguser',
            email='staff@example.com',
            password='pass123'
        )
        response = self.client.post(self.signup_url, {
            'username': 'newuser',
            'email': 'staff@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'staff'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "account with this email already exists")