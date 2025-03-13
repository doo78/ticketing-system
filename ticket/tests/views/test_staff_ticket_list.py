from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from ticket.models import Ticket, Staff

User = get_user_model()

class ManageTicketViewTest(TestCase):
    def setUp(self):
        """Create staff user and test ticket"""
        self.staff_user = User.objects.create_user(username='staffuser', password='password123')
        self.staff = Staff.objects.create(user=self.staff_user)
        
        self.ticket = Ticket.objects.create(
            subject='Test Ticket',
            description='This is a test ticket.',
            status='open',
        )
        
        self.client.login(username='staffuser', password='password123')
    
    def test_assign_ticket(self):
        """Test assigning ticket to staff"""
        response = self.client.post(reverse('manage_ticket', args=[self.ticket.id]), {'action': 'assign'})
        self.ticket.refresh_from_db()
        
        self.assertEqual(self.ticket.assigned_staff, self.staff)
        self.assertEqual(self.ticket.status, 'pending')
        self.assertRedirects(response, reverse('staff_ticket_list'))
    
    def test_close_ticket(self):
        """Test closing a ticket"""
        response = self.client.post(reverse('manage_ticket', args=[self.ticket.id]), {'action': 'close'})
        self.ticket.refresh_from_db()
        
        self.assertEqual(self.ticket.status, 'closed')
        self.assertEqual(self.ticket.closed_by, self.staff)
        self.assertIsNotNone(self.ticket.date_closed)
        self.assertRedirects(response, reverse('staff_ticket_list'))


class StaffTicketListViewTest(TestCase):
    def setUp(self):
        """Create a staff user and some test tickets."""
        self.staff_user = User.objects.create_user(username='staffuser', password='password123')
        self.staff = Staff.objects.create(user=self.staff_user)

        Ticket.objects.create(subject='Open Ticket', status='open')
        Ticket.objects.create(subject='Pending Ticket', status='pending')
        Ticket.objects.create(subject='Closed Ticket', status='closed')
        
        self.client.login(username='staffuser', password='password123')
    
    def test_view_all_tickets(self):
        """Test viewing tickets without filters"""
        response = self.client.get(reverse('staff_ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tickets']), 3)
    
    def test_filter_open_tickets(self):
        """Test filtering tickets by 'open' status"""
        response = self.client.get(reverse('staff_ticket_list') + '?status=open')
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].status, 'open')
    
    def test_filter_pending_tickets(self):
        """Test filtering tickets by 'pending' status"""
        response = self.client.get(reverse('staff_ticket_list') + '?status=pending')
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].status, 'pending')
    
    def test_filter_closed_tickets(self):
        """Test filtering tickets by 'closed' status"""
        response = self.client.get(reverse('staff_ticket_list') + '?status=closed')
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].status, 'closed')
    
    def test_ticket_counts(self):
        """Test ticket count values in context"""
        response = self.client.get(reverse('staff_ticket_list'))
        self.assertEqual(response.context['open_count'], 1)
        self.assertEqual(response.context['pending_count'], 1)
        self.assertEqual(response.context['closed_count'], 1)
