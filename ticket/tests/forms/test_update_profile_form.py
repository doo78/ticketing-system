from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from ticket.forms import StaffUpdateProfileForm
from ticket.models import CustomUser, Staff
from PIL import Image
from io import BytesIO

class StaffUpdateProfileFormTest(TestCase):
    
    def setUp(self):
        """Set up a test user and staff member."""
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123",
            first_name="Test",
            last_name="User"
        )
        self.staff = Staff.objects.create(
            user=self.user,
            department="business",  
            profile_picture=None
        )

    def test_valid_form_submission(self):
        """Test that the form saves valid data correctly."""
        form_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "preferred_name": "Upd",
            "department": "dentistry" 
        }
        form = StaffUpdateProfileForm(data=form_data, instance=self.user)
        
        self.assertTrue(form.is_valid(), msg=form.errors)
        
        updated_user = form.save()
        self.staff.refresh_from_db()

        self.assertEqual(updated_user.first_name, "Updated")
        self.assertEqual(updated_user.last_name, "Name")
        self.assertEqual(updated_user.email, "updated@example.com")
        self.assertEqual(updated_user.preferred_name, "Upd")
        self.assertEqual(self.staff.department, "dentistry")  

    def test_profile_picture_upload(self):
        """Test that a profile picture is uploaded and saved."""
        image = Image.new("RGB", (100, 100), color="red")
        image_io = BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        uploaded_image = SimpleUploadedFile(
            name="test_image.jpg",
            content=image_io.read(),
            content_type="image/jpeg"
        )

        form_data = {
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
            "preferred_name": "Upd",
            "department": "social_science" 
        }

        form = StaffUpdateProfileForm(data=form_data, files={"profile_picture": uploaded_image}, instance=self.user)

        self.assertTrue(form.is_valid(), msg=form.errors)

        updated_user = form.save()
        self.staff.refresh_from_db()

        self.assertIn("test_image", self.staff.profile_picture.name)

    def test_invalid_data(self):
        """Test form validation with missing required fields."""
        form_data = {
            "first_name": "",
            "last_name": "",
            "email": "invalid-email",
            "preferred_name": "Upd",
            "department": ""  
        }
        form = StaffUpdateProfileForm(data=form_data, instance=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)
        self.assertIn("last_name", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("department", form.errors)  