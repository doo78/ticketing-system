from django.test import TestCase, Client
from django.urls import reverse

class BasicViewsTestCase(TestCase):
    """Test cases for basic navigation views"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.home_url = reverse('home')
        self.about_url = reverse('about')
        self.faq_url = reverse('faq')

    def test_home_view(self):
        """Test home view"""
        response = self.client.get(self.home_url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Check correct template is used
        self.assertTemplateUsed(response, 'home.html')
    
    def test_about_view(self):
        """Test about view"""
        response = self.client.get(self.about_url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Check correct template is used
        self.assertTemplateUsed(response, 'about.html')
    
    def test_faq_view(self):
        """Test FAQ view"""
        response = self.client.get(self.faq_url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Check correct template is used
        self.assertTemplateUsed(response, 'faq.html') 