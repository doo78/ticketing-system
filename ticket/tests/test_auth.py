from django.test import TestCase, Client
from django.urls import reverse
from ticket.models import CustomUser, Staff, Student, Department


class StaffAuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('sign_up')
        self.login_url = reverse('log_in')
        self.business_dept = Department.objects.create(name='Business')
        self.law_dept = Department.objects.create(name='Law')
        self.staff_data = {
            'username': 'staffuser',
            'email': 'staff@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'staff',
            'first_name': 'Staff',
            'last_name': 'User',
            'department': str(self.business_dept.id)
        }

    def test_staff_signup_success(self):
        response = self.client.post(self.signup_url, self.staff_data)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(Staff.objects.count(), 1)
        self.assertRedirects(response, reverse('log_in'))

        # Verify user details
        user = CustomUser.objects.first()
        staff_profile = Staff.objects.first()
        self.assertIsNone(staff_profile.department)
        self.assertEqual(user.email, self.staff_data['email'])
        self.assertEqual(user.first_name, self.staff_data['first_name'])
        self.assertEqual(user.last_name, self.staff_data['last_name'])
        self.assertEqual(user.role, 'staff')

    def test_staff_login_success(self):
        # Create a staff user
        user = CustomUser.objects.create_user(
            username=self.staff_data['username'],
            password=self.staff_data['password1'],
            email=self.staff_data['email'],
            first_name=self.staff_data['first_name'],
            last_name=self.staff_data['last_name'],
            role='staff'
        )
        Staff.objects.create(user=user, department=self.business_dept, role='Staff Member')

        response = self.client.post(self.login_url, {
            'username': self.staff_data['username'],
            'password': self.staff_data['password1']
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
        # Create user with the email first
        CustomUser.objects.create_user(
            username='existinguser',
            email=self.staff_data['email'],
            password='pass123'
        )
        response = self.client.post(self.signup_url, self.staff_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User with this Email already exists")  # Updated error message


class StudentAuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('sign_up')
        self.login_url = reverse('log_in')
        self.business_dept = Department.objects.create(name='Business')
        self.law_dept = Department.objects.create(name='Law')
        self.student_data = {
            'username': 'studentuser',
            'email': 'student@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'student',
            'first_name': 'Student',
            'last_name': 'User',
            'department': str(self.business_dept.id),
            'program': 'Business Administration',
            'year_of_study': 2
        }

    def test_student_signup_success(self):
        response = self.client.post(self.signup_url, self.student_data)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(Student.objects.count(), 1)
        self.assertRedirects(response, reverse('log_in'))

        # Verify user details
        user = CustomUser.objects.first()
        student = Student.objects.first()
        self.assertEqual(user.email, self.student_data['email'])
        self.assertEqual(user.first_name, self.student_data['first_name'])
        self.assertEqual(user.role, 'student')
        self.assertEqual(student.program, self.student_data['program'])
        self.assertEqual(student.year_of_study, self.student_data['year_of_study'])

    def test_student_login_success(self):
        # Create a student user
        user = CustomUser.objects.create_user(
            username=self.student_data['username'],
            password=self.student_data['password1'],
            email=self.student_data['email'],
            first_name=self.student_data['first_name'],
            last_name=self.student_data['last_name'],
            role='student'
        )
        Student.objects.create(
            user=user,
            department=self.business_dept,
            program=self.student_data['program'],
            year_of_study=self.student_data['year_of_study']
        )

        response = self.client.post(self.login_url, {
            'username': self.student_data['username'],
            'password': self.student_data['password1']
        })
        self.assertRedirects(response, reverse('student_dashboard'))

    def test_student_signup_missing_required_fields(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'student',
            'first_name': 'Test',
            'last_name': 'User'
            # Missing student fields
        }
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(CustomUser.objects.count(), 0)
        self.assertContains(response, "This field is required for students")

    def test_password_mismatch(self):
        data = self.student_data.copy()
        data['password2'] = 'differentpass'
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two password fields didn’t match")


    def test_student_required_fields_validation(self):
        """Test that student-specific fields are required when role is student"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'student',
            'first_name': 'Test',
            'last_name': 'User',
            'department': '',  # Empty department
            'program': '',  # Empty program
            'year_of_study': ''  # Empty year of study
        }

        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(CustomUser.objects.count(), 0)
        # Verify required field errors are shown
        self.assertContains(response, "This field is required")


class GeneralAuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('sign_up')

    def test_password_mismatch(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'differentpass',
            'role': 'student',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "The two password fields didn’t match")

