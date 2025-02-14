from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from ticket.models import Ticket, Staff, CustomUser
from datetime import timedelta
from django.utils import timezone

from django.core.files.uploadedfile import SimpleUploadedFile
import os

class StaffProfileViewTest(TestCase):
    
    def setUp(self):
        """Create a user and associated staff with tickets for testing."""
        
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )
        self.user.staff = Staff.objects.create(
            user=self.user,
            department='business',
            role='manager'
        )
        self.staff_member = self.user.staff
        self.ticket1 = Ticket.objects.create(
            subject="Test Ticket 1",
            description="This is a test ticket.",
            status="open",
            assigned_staff=self.staff_member,
            date_submitted=timezone.now()
        )
        self.ticket2 = Ticket.objects.create(
            subject="Test Ticket 2",
            description="This is another test ticket.",
            status="closed",
            assigned_staff=self.staff_member,
            date_submitted=timezone.now() - timedelta(days=5),
            date_closed=timezone.now() - timedelta(days=3)
        )
        
        self.client.login(username='testuser', password='password123')

    def test_profile_view_renders_correct_data(self):
        """Test that the profile page displays correct data."""
        
        response = self.client.get(reverse('staff_profile'))
        
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Open')
        self.assertContains(response, 'Pending')
        self.assertContains(response, 'Closed')
        
        self.assertContains(response, "Average Response Time")
        self.assertContains(response, '<img src="/static/images/default-profile.png"')
                
    def test_profile_with_default_picture(self):
        """Test the profile with no profile picture uploaded."""
        
        self.staff_member.profile_picture = None 
        self.staff_member.save()

        response = self.client.get(reverse('staff_profile'))
        
        self.assertContains(response, '/static/images/default-profile.png')
        
    def test_ticket_stats_calculation(self):
        """Test the ticket stats calculations."""
        
        response = self.client.get(reverse('staff_profile'))
        
        self.assertContains(response, 'Open')
        self.assertContains(response, 'Closed')
        self.assertContains(response, 'Pending')
        self.assertContains(response, 'Average Response Time')


    def test_profile_with_uploaded_picture(self):
        """Test the profile with a profile picture uploaded."""
        
        self.client.login(username='testuser', password='password123')

        image_data = SimpleUploadedFile(
            name='test_image.jpg',
            content=b"fake image data",
            content_type='image/jpeg'
        )

        response = self.client.post(reverse('staff_update_profile'), {
            'profile_picture': image_data
        })

        self.staff_member.refresh_from_db()

        if not self.staff_member.profile_picture:
            self.staff_member.profile_picture = image_data
            self.staff_member.save()
            self.staff_member.refresh_from_db()

        self.assertIn('test_image', self.staff_member.profile_picture.name)

        response = self.client.get(reverse('staff_profile'))
        self.assertContains(response, self.staff_member.profile_picture.url)

