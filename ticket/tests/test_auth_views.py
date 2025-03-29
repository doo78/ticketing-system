from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from ticket.models import Ticket, Staff, Student, CustomUser
import json
from ticket.views import EmailVerificationTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()

class AuthenticationViewsTestCase(TestCase):
    """Test cases for authentication views"""

    def setUp(self):
        """Set up test data"""
        # Create users
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            role='staff'
        )
        self.staff = Staff.objects.create(user=self.staff_user, department='business')
        
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
        
        # URLs
        self.login_url = reverse('log_in')
        self.logout_url = reverse('logout')
        self.signup_url = reverse('sign_up')
        self.forget_password_url = reverse('forget-password')
        
        # Client
        self.client = Client()

    def test_login_get(self):
        """Test login page GET request"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
    
    def test_login_post_success_admin(self):
        """Test successful login for admin user"""
        response = self.client.post(self.login_url, {
            'username': 'adminuser',
            'password': 'adminpass123'
        })
        
        # Check redirect to admin dashboard
        self.assertRedirects(response, reverse('admin_dashboard'))
        
        # Check user is logged in
        self.assertTrue('_auth_user_id' in self.client.session)
    
    def test_login_post_success_staff(self):
        """Test successful login for staff user"""
        response = self.client.post(self.login_url, {
            'username': 'staffuser',
            'password': 'staffpass123'
        })
        
        # Check redirect to staff dashboard
        self.assertRedirects(response, reverse('staff_dashboard'))
        
        # Check user is logged in
        self.assertTrue('_auth_user_id' in self.client.session)
    
    def test_login_post_success_student(self):
        """Test successful login for student user"""
        response = self.client.post(self.login_url, {
            'username': 'studentuser',
            'password': 'studentpass123'
        })
        
        # Check redirect to student dashboard
        self.assertRedirects(response, reverse('student_dashboard'))
        
        # Check user is logged in
        self.assertTrue('_auth_user_id' in self.client.session)
    
    def test_login_post_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(self.login_url, {
            'username': 'adminuser',
            'password': 'wrongpassword'
        })
        
        # Check user stays on login page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Invalid username or password.")
        
        # Check user is not logged in
        self.assertFalse('_auth_user_id' in self.client.session)
    
    def test_logout(self):
        """Test logout functionality"""
        # First login
        self.client.login(username='adminuser', password='adminpass123')
        
        # Check user is logged in
        self.assertTrue('_auth_user_id' in self.client.session)
        
        # Then logout
        response = self.client.get(self.logout_url)
        
        # Check redirect to login page
        self.assertRedirects(response, self.login_url)
        
        # Check user is logged out
        self.assertFalse('_auth_user_id' in self.client.session)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "You have been logged out successfully.")
    
    def test_signup_get(self):
        """Test signup page GET request"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
    
    def test_signup_post_success(self):
        """Test successful user registration"""
        user_data = {
            'username': 'newuser',
            'password1': 'complex-password123',
            'password2': 'complex-password123',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student',
            'department': 'business',
            'program': 'Computer Science',
            'year_of_study': 2
        }
        
        response = self.client.post(self.signup_url, user_data)
        
        # Check redirect to login page
        self.assertRedirects(response, self.login_url)
        
        # Check user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Check student profile was created
        new_user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(new_user, 'student'))
        self.assertEqual(new_user.student.department, 'business')
        self.assertEqual(new_user.student.program, 'Computer Science')
        self.assertEqual(new_user.student.year_of_study, 2)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue("Account created successfully" in str(messages[0]))
    
    def test_signup_post_validation_error(self):
        """Test signup with validation errors"""
        user_data = {
            'username': 'newuser',
            'password1': 'complex-password123',
            'password2': 'different-password',  # Passwords don't match
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student'
        }
        
        response = self.client.post(self.signup_url, user_data)
        
        # Check user stays on signup page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        
        # Check form has errors
        self.assertTrue(response.context['form'].errors)
        
        # Check user was not created
        self.assertFalse(User.objects.filter(username='newuser').exists())
    
    def test_verify_email(self):
        """Test email verification"""
        # Create unverified user
        unverified_user = User.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='password123',
            role='student',
            is_email_verified=False
        )
        
        # Generate verification token
        token_generator = EmailVerificationTokenGenerator()
        token = token_generator.make_token(unverified_user)
        uid = urlsafe_base64_encode(force_bytes(unverified_user.pk))
        
        # Access verification URL
        verify_url = reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(verify_url)
        
        # Check redirect to login page
        self.assertRedirects(response, self.login_url)
        
        # Check user is now verified
        unverified_user.refresh_from_db()
        self.assertTrue(unverified_user.is_email_verified)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue("Your email has been verified successfully" in str(messages[0]))
    
    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token"""
        # Create unverified user
        unverified_user = User.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='password123',
            role='student',
            is_email_verified=False
        )
        
        # Generate invalid verification URL
        uid = urlsafe_base64_encode(force_bytes(unverified_user.pk))
        invalid_token = "invalid-token"
        
        # Access verification URL with invalid token
        verify_url = reverse('verify_email', kwargs={'uidb64': uid, 'token': invalid_token})
        response = self.client.get(verify_url)
        
        # Check redirect to login page
        self.assertRedirects(response, self.login_url)
        
        # Check user is still unverified
        unverified_user.refresh_from_db()
        self.assertFalse(unverified_user.is_email_verified)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "The verification link is invalid or has expired.")

class PasswordResetTestCase(TestCase):
    """Test cases for password reset flow"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='student'
        )
        
        # URLs
        self.forget_password_url = reverse('forget-password')
        self.reset_password_sent_url = reverse('email-sent')
        
        # Client
        self.client = Client()
    
    def test_forget_password_get(self):
        """Test forget password page GET request"""
        response = self.client.get(self.forget_password_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forget-password/mail-page.html')
    
    def test_forget_password_post_valid_email(self):
        """Test forget password with valid email"""
        response = self.client.post(self.forget_password_url, {'email': 'test@example.com'})
        
        # Should render email sent page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forget-password/email-sent.html')
        
        # Check user has a remember token now
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.remember_token)
    
    def test_forget_password_post_invalid_email(self):
        """Test forget password with invalid email"""
        response = self.client.post(self.forget_password_url, {'email': 'nonexistent@example.com'})
        
        # Should show error page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'exception/error-page.html')
    
    def test_password_reset_sent_view(self):
        """Test password reset sent view"""
        response = self.client.get(self.reset_password_sent_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forget-password/email-sent.html')
    
    def test_reset_password_view_get(self):
        """Test reset password view GET with valid token"""
        # Generate token for user
        token = self.user.generate_remember_token()
        
        # Access reset password page
        reset_url = reverse('forget_password_reset_password') + f'?token={token}'
        response = self.client.get(reset_url)
        
        # Check template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forget-password/new-password.html')
    
    def test_reset_password_view_post_success(self):
        """Test reset password view POST success"""
        # Generate token for user
        token = self.user.generate_remember_token()
        
        # Submit new password
        reset_url = reverse('forget_password_reset_password')
        response = self.client.post(reset_url, {
            'token': token,
            'new_password': 'new-password123',
            'confirm_password': 'new-password123'
        })
        
        # Check redirect to login
        self.assertRedirects(response, reverse('log_in'))
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Password updated successfully.')
        
        # Check password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new-password123'))
        
        # Check token was cleared
        self.assertIsNone(self.user.remember_token)
    
    def test_reset_password_view_post_passwords_dont_match(self):
        """Test reset password view POST with mismatched passwords"""
        # Generate token for user
        token = self.user.generate_remember_token()
        
        # Submit mismatched passwords
        reset_url = reverse('forget_password_reset_password')
        response = self.client.post(reset_url, {
            'token': token,
            'new_password': 'new-password123',
            'confirm_password': 'different-password'
        })
        
        # Check redirect back to form
        self.assertEqual(response.status_code, 302)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Passwords do not match.')
    
    def test_reset_password_view_invalid_token(self):
        """Test reset password view with invalid token"""
        # Access reset password page with invalid token
        reset_url = reverse('forget_password_reset_password') + '?token=invalid-token'
        response = self.client.get(reset_url)
        
        # Should show error page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'exception/error-page.html') 