from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from ticket.forms import StaffUpdateProfileForm
from ticket.models import Staff, CustomUser

class StaffUpdateProfileFormTest(TestCase):
    def setUp(self):
        """Set up test data."""
        self.user = CustomUser.objects.create_user(
            username='teststaff',
            password='testpass123',
            email='staff@test.com',
            first_name='Test',
            last_name='Staff',
            role='staff'  # Ensure user has staff role
        )
        self.staff = Staff.objects.create(
            user=self.user,
            department='business',
            role='Staff Member'
        )

    def test_valid_form_submission(self):
        """Test form submission with valid data."""
        form_data = {
            'first_name': 'Updated',
            'last_name': 'Staff',
            'email': 'updated@test.com',
            'preferred_name': 'Upd',
            'department': 'business'
        }
        form = StaffUpdateProfileForm(data=form_data, instance=self.user)  # Pass user instance
        self.assertTrue(form.is_valid())
        updated_user = form.save()
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.email, 'updated@test.com')

    def test_profile_picture_upload(self):
        """Test uploading a profile picture."""
        image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        image = SimpleUploadedFile('test_image.gif', image_content, content_type='image/gif')
        
        form_data = {
            'first_name': 'Test',
            'last_name': 'Staff',
            'email': 'staff@test.com',
            'preferred_name': 'Test',
            'department': 'business'
        }
        file_data = {'profile_picture': image}
        
        form = StaffUpdateProfileForm(data=form_data, files=file_data, instance=self.user)  # Pass user instance
        self.assertTrue(form.is_valid())
        staff = form.save()
        self.assertTrue(staff.staff.profile_picture)
        self.assertIn('test_image', staff.staff.profile_picture.name)

    def test_invalid_data(self):
        """Test form validation with missing required fields."""
        form_data = {
            'first_name': '',  # Required field
            'last_name': 'Staff',
            'email': 'invalid-email',  # Invalid email
            'department': '',  # Required field
        }
        form = StaffUpdateProfileForm(data=form_data, instance=self.user)  # Pass user instance
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('department', form.errors) 