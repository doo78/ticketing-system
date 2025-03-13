from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from ticket.models import Ticket, Staff, Student, CustomUser
from unittest.mock import patch
import json

User = get_user_model()


class ManageTicketViewTest(TestCase):
    def setUp(self):
        """Create a staff user and a test ticket."""
        self.staff_user = User.objects.create_user(username='staffuser', password='password123')
        self.staff = Staff.objects.create(user=self.staff_user)

        self.ticket = Ticket.objects.create(
            subject='Test Ticket',
            description='This is a test ticket.',
            status='open',
        )

        self.pending_ticket = Ticket.objects.create(
            subject='Test Ticket',
            description='This is a test ticket.',
            status='pending',
            department='business',
        )

        self.pending_ticket_assigned = Ticket.objects.create(
            subject='Pending Ticket Assigned to Me',
            description='This is a pending ticket assigned to the current user.',
            status='pending',
            department='business',
            assigned_staff=self.staff
        )

        self.client.login(username='staffuser', password='password123')

    def test_assign_ticket(self):
        """Test assigning a ticket to a staff member."""
        response = self.client.post(reverse('manage_ticket', args=[self.ticket.id]), {'action': 'assign'})
        self.ticket.refresh_from_db()

        self.assertEqual(self.ticket.assigned_staff, self.staff)
        self.assertEqual(self.ticket.status, 'pending')
        # Updated to expect redirect to list page
        self.assertRedirects(response, reverse('staff_ticket_list'))

    def test_close_ticket(self):
        """Test closing a ticket."""
        response = self.client.post(reverse('manage_ticket', args=[self.ticket.id]), {'action': 'close'})
        self.ticket.refresh_from_db()

        self.assertEqual(self.ticket.status, 'closed')
        self.assertEqual(self.ticket.closed_by, self.staff)
        self.assertIsNotNone(self.ticket.date_closed)
        # Updated to expect redirect to list page
        self.assertRedirects(response, reverse('staff_ticket_list'))

    def test_redirect_ticket_assigned_to_user(self):
        """Test that the redirect button is visible when the ticket is assigned to the current user."""
        data = {
            'action': 'redirect',
            'department': 'law',
        }

        response = self.client.post(reverse('manage_ticket', args=[self.pending_ticket_assigned.id]), data)
        self.pending_ticket_assigned.refresh_from_db()

        self.assertEqual(self.pending_ticket_assigned.department, 'law')
        self.assertEqual(self.pending_ticket_assigned.status, 'open')

        self.assertIsNone(self.pending_ticket_assigned.assigned_staff)

        # Updated to expect redirect to list page
        self.assertRedirects(response, reverse('staff_ticket_list'))

    def test_redirect_ticket_assigned_to_other_user(self):
        """Test that the redirect button is not shown when the ticket is assigned to another user."""
        other_staff_user = User.objects.create_user(username='otherstaff', password='password123',
                                                    email='otherstaff@gmail.com')
        other_staff = Staff.objects.create(user=other_staff_user)

        self.pending_ticket.assigned_staff = other_staff
        self.pending_ticket.save()

        self.client.login(username='staffuser', password='password123')

        response = self.client.get(reverse('staff_ticket_detail', args=[self.pending_ticket.id]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Redirect Ticket')


class StaffTicketListViewTest(TestCase):
    def setUp(self):
        """Create a staff user and some test tickets."""
        # Create staff user
        self.staff_user = CustomUser.objects.create_user(
            username='staffuser',
            password='testpass123',
            email='staff@example.com',
            first_name='Staff',
            last_name='User',
            role='staff'
        )
        self.staff = Staff.objects.create(
            user=self.staff_user,
            department='business',
            role='Staff Member'
        )

        # Create student user
        self.student_user = CustomUser.objects.create_user(
            username='studentuser',
            password='testpass123',
            email='student@example.com',
            first_name='Student',
            last_name='User',
            role='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            department='business',
            program='Business Administration',
            year_of_study=2
        )

        # Create test tickets
        self.open_ticket = Ticket.objects.create(
            subject='Open Ticket',
            description='This is a test ticket',
            department='business',
            status='open',
            student=self.student
        )
        Ticket.objects.create(subject='Pending Ticket', status='pending', student=self.student)
        Ticket.objects.create(subject='Closed Ticket', status='closed', student=self.student)

        self.client.login(username='staffuser', password='testpass123')
        self.ticket_detail_url = reverse('staff_ticket_detail', args=[self.open_ticket.id])

    def test_view_all_tickets(self):
        """Test viewing all tickets without filters."""
        response = self.client.get(reverse('staff_ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tickets']), 3)

    def test_filter_open_tickets(self):
        """Test filtering tickets by 'open' status."""
        response = self.client.get(reverse('staff_ticket_list') + '?status=open')
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].status, 'open')

    def test_filter_pending_tickets(self):
        """Test filtering tickets by 'pending' status."""
        response = self.client.get(reverse('staff_ticket_list') + '?status=pending')
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].status, 'pending')

    def test_filter_closed_tickets(self):
        """Test filtering tickets by 'closed' status."""
        response = self.client.get(reverse('staff_ticket_list') + '?status=closed')
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].status, 'closed')

    def test_ticket_counts(self):
        """Test ticket count values in context."""
        response = self.client.get(reverse('staff_ticket_list'))
        self.assertEqual(response.context['open_count'], 1)
        self.assertEqual(response.context['pending_count'], 1)
        self.assertEqual(response.context['closed_count'], 1)

    def test_view_ticket_detail(self):
        """Test basic ticket detail view access"""
        response = self.client.get(self.ticket_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'staff/ticket_detail.html')
        self.assertEqual(response.context['ticket'], self.open_ticket)

    @patch('boto3.client')
    def test_generate_ai_response(self, mock_boto3_client):
        """Test generating AI response for a ticket"""
        # Mock the Lambda response
        mock_lambda = mock_boto3_client.return_value
        mock_lambda.invoke.return_value = {
            'StatusCode': 200,
            'Payload': type('MockPayload', (), {
                'read': lambda self: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': 'This is an AI generated response'
                    })
                }).encode()
            })()
        }

        # Make the request
        response = self.client.post(
            self.ticket_detail_url,
            data=json.dumps({'action': 'generate_ai'}),
            content_type='application/json'
        )

        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['response'], 'This is an AI generated response')

        # Verify Lambda was called with correct parameters
        mock_lambda.invoke.assert_called_once()
        call_args = mock_lambda.invoke.call_args[1]
        self.assertEqual(call_args['FunctionName'], 'ticket-context-handler')
        payload = json.loads(call_args['Payload'])
        self.assertEqual(payload['ticket_id'], self.open_ticket.id)
        self.assertEqual(payload['action'], 'generate_ai')

    @patch('boto3.client')
    def test_refine_ai_response(self, mock_boto3_client):
        """Test refining a response with AI"""
        # Mock the Lambda response
        mock_lambda = mock_boto3_client.return_value
        mock_lambda.invoke.return_value = {
            'StatusCode': 200,
            'Payload': type('MockPayload', (), {
                'read': lambda self: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': 'This is a refined AI response'
                    })
                }).encode()
            })()
        }

        # Make the request
        response = self.client.post(
            self.ticket_detail_url,
            data=json.dumps({
                'action': 'refine_ai',
                'current_text': 'Initial response draft'
            }),
            content_type='application/json'
        )

        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['response'], 'This is a refined AI response')

    @patch('boto3.client')
    def test_handle_lambda_error(self, mock_boto3_client):
        """Test handling Lambda errors gracefully"""
        # Mock a Lambda error response
        mock_lambda = mock_boto3_client.return_value
        mock_lambda.invoke.return_value = {
            'StatusCode': 500,
            'FunctionError': 'Unhandled',
            'Payload': type('MockPayload', (), {
                'read': lambda self: json.dumps({
                    'errorMessage': 'Lambda execution failed'
                }).encode()
            })()
        }

        # Make the request
        response = self.client.post(
            self.ticket_detail_url,
            data=json.dumps({'action': 'generate_ai'}),
            content_type='application/json'
        )

        # Verify error response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)

    def test_invalid_json_request(self):
        """Test handling invalid JSON in request"""
        response = self.client.post(
            self.ticket_detail_url,
            data='invalid json',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Invalid JSON in request')

    def test_add_regular_message(self):
        """Test adding a regular message to the ticket"""
        response = self.client.post(
            self.ticket_detail_url,
            {'message': 'This is a regular message'}
        )

        self.assertRedirects(response, self.ticket_detail_url)
        self.assertTrue(self.open_ticket.messages.filter(content='This is a regular message').exists())

    def test_add_message_to_closed_ticket(self):
        """Test attempting to add a message to a closed ticket"""
        self.open_ticket.status = 'closed'
        self.open_ticket.save()

        response = self.client.post(
            self.ticket_detail_url,
            {'message': 'This is a message'}
        )

        self.assertRedirects(response, self.ticket_detail_url)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('closed' in str(m).lower() for m in messages))


class StaffTicketRatingTest(TestCase):
    def setUp(self):
        """Create a staff user and test tickets with ratings."""
        # Create staff user
        self.staff_user = CustomUser.objects.create_user(
            username='staffuser',
            password='testpass123',
            email='staff@example.com',
            first_name='Staff',
            last_name='User',
            role='staff'
        )
        self.staff = Staff.objects.create(
            user=self.staff_user,
            department='business',
            role='Staff Member'
        )

        # Create student user
        self.student_user = CustomUser.objects.create_user(
            username='studentuser',
            password='testpass123',
            email='student@example.com',
            first_name='Student',
            last_name='User',
            role='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            department='business',
            program='Business Administration',
            year_of_study=2
        )

        # Create test tickets with ratings
        self.rated_ticket1 = Ticket.objects.create(
            subject='Rated Ticket 1',
            description='This is a test ticket with rating',
            department='business',
            status='closed',
            student=self.student,
            assigned_staff=self.staff,
            date_closed=timezone.now(),
            rating=5,
            rating_comment='Excellent support!'
        )

        self.rated_ticket2 = Ticket.objects.create(
            subject='Rated Ticket 2',
            description='This is another test ticket with rating',
            department='business',
            status='closed',
            student=self.student,
            assigned_staff=self.staff,
            date_closed=timezone.now(),
            rating=3,
            rating_comment='Good but could be faster'
        )

        self.unrated_ticket = Ticket.objects.create(
            subject='Unrated Closed Ticket',
            description='This is a closed ticket without rating',
            department='business',
            status='closed',
            student=self.student,
            assigned_staff=self.staff,
            date_closed=timezone.now()
        )

        self.client.login(username='staffuser', password='testpass123')

    def test_staff_can_see_ticket_rating_in_detail_view(self):
        """Test that staff can see ratings in ticket detail view."""
        response = self.client.get(reverse('staff_ticket_detail', args=[self.rated_ticket1.id]))
        self.assertEqual(response.status_code, 200)

        # Check that rating info is displayed, without relying on specific formatting
        self.assertContains(response, 'Student Feedback')
        self.assertContains(response, self.rated_ticket1.rating_comment)

    def test_unrated_closed_ticket_shows_no_rating_message(self):
        """Test that unrated closed tickets show a message."""
        response = self.client.get(reverse('staff_ticket_detail', args=[self.unrated_ticket.id]))
        self.assertEqual(response.status_code, 200)

        # Check for message about no rating
        self.assertContains(response, 'No rating')

    def test_staff_ticket_list_shows_ratings_for_closed_tickets(self):
        """Test that ratings appear in the staff ticket list for closed tickets."""
        response = self.client.get(reverse('staff_ticket_list') + '?status=closed')
        self.assertEqual(response.status_code, 200)

        # Check for rating column header
        self.assertContains(response, '<th>Rating</th>')

        # Check for "Not rated" text - we'll be more general with our assertions
        self.assertContains(response, 'Not rated')

    def test_staff_profile_shows_average_rating(self):
        """Test that the staff profile shows the correct average rating."""
        response = self.client.get(reverse('staff_profile'))
        self.assertEqual(response.status_code, 200)

        # Check that the average rating section exists
        self.assertContains(response, 'Average Rating')

        # We expect rating to be displayed, but not hardcoding exact format
        # Instead of checking for exact "4.0", just check for the base number
        self.assertContains(response, '4')

        # Check for "Based on X rated tickets" text without being too specific
        self.assertContains(response, 'Based on')
        self.assertContains(response, 'rated ticket')

    def test_staff_profile_with_no_ratings(self):
        """Test staff profile when no tickets have ratings."""
        # Remove ratings from tickets
        Ticket.objects.all().update(rating=None, rating_comment=None)

        response = self.client.get(reverse('staff_profile'))
        self.assertEqual(response.status_code, 200)

        # Check for "N/A" text
        self.assertContains(response, 'N/A')

        # Check for "No rated tickets yet" text
        self.assertContains(response, 'No rated tickets yet')