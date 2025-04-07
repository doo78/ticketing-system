import imaplib
import email
import os
import datetime
from email.header import decode_header
from email.utils import parseaddr
from django.conf import settings
from django.utils import timezone
from django.db.models import Max, F
from django.core.mail import send_mail
from ticket.models import Ticket, Student, StudentMessage, AdminMessage, Department
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

# Helper function to decode MIME-encoded subjects
def decode_mime_words(s):
    if not s:
        return ""
    decoded_fragments = []
    for fragment, encoding in decode_header(s):
        if isinstance(fragment, bytes):
            try:
                decoded_fragments.append(fragment.decode(encoding or 'utf-8', errors="replace"))
            except Exception:
                decoded_fragments.append(fragment.decode("utf-8", errors="replace"))
        else:
            decoded_fragments.append(fragment)
    return "".join(decoded_fragments)

# Helper function to extract email body
def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                charset = part.get_content_charset() or 'utf-8'
                try:
                    return part.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    return part.get_payload(decode=True).decode("utf-8", errors="replace")
    else:
        charset = msg.get_content_charset() or 'utf-8'
        try:
            return msg.get_payload(decode=True).decode(charset, errors="replace")
        except Exception:
            return msg.get_payload(decode=True).decode("utf-8", errors="replace")
    return ""

# Function to create a ticket from an email
def create_ticket_from_email(msg, dept_code):
    """Create a ticket from an email message for a specific department."""
    subject = decode_mime_words(msg.get("Subject"))
    body = get_body(msg)
    raw_from = msg.get("From")
    _, from_email = parseaddr(raw_from)
    student = Student.objects.filter(user__email=from_email).first()
    if not student:
        return
    msg_id = msg.get("Message-ID")
    if not msg_id:
        msg_id = f"{msg.get('From')}_{msg.get('Date')}"
    if Ticket.objects.filter(message_id=msg_id).exists():
        return
    Ticket.objects.create(
        subject=subject or "No Subject",
        student=student,
        description=body,
        message_id=msg_id,
        department=dept_code,
    )

def process_emails_for_department(dept_code, email_address, password):
    """Fetch and process emails for a specific department."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        print(f"Logging in to {email_address} with password {password}")
        mail.login(email_address, password)
        mail.select("INBOX")
        status, message_numbers = mail.search(None, 'UNSEEN')
        if status == "OK":
            print(f"Processing emails for {dept_code}...")
            for num in message_numbers[0].split():
                status, data = mail.fetch(num, '(RFC822)')
                if status == "OK":
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                
                    create_ticket_from_email(msg, dept_code)
                    mail.store(num, '+FLAGS', '\\Seen')
        mail.logout()
    except Exception as e:
        print(f"Error processing emails for {dept_code}: {e}")

# Main function to fetch emails from all departments
def fetch_and_create_tickets():
    """Fetch emails from all department email accounts and create tickets."""
    for dept_code, credentials in Department.get_all_departments_with_email():
        email = credentials['email']
        password = credentials['password']
        process_emails_for_department(dept_code, email, password)

# Function to send reminder emails
def send_reminder_emails():
    """
    Send reminder emails to students for tickets that have been awaiting their response for over a week.
    A ticket qualifies if:
    - Status is 'open' or 'pending'
    - Latest message is from a staff member
    - Latest message is more than 7 days old
    """

    # get the tickets where the latest message is from a staff member and is over a week old
    latest_messages = AdminMessage.objects.annotate(
        max_created_at=Max('ticket__admin_messages__created_at')
    ).filter(
        created_at=F('max_created_at'),
        created_at__lt=timezone.now() - datetime.timedelta(days=7),
        author__role='staff',
        ticket__status__in=['open', 'pending']
    )

    tickets_needing_reminder = Ticket.objects.filter(
        admin_messages__in=latest_messages
    ).distinct()


    for ticket in tickets_needing_reminder:
        student = ticket.student
        student_name = student.user.preferred_name or student.user.first_name
        student_email = student.user.email

        subject = 'Reminder: Your Ticket Needs Attention'
        message = (
            f"Dear {student_name},\n\n"
            f"We noticed that your ticket '{ticket.subject}' has not received a response from you "
            f"in over a week. Please check the ticket and provide any necessary information or updates.\n\n"
            f"Thank you"
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[student_email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending reminder for ticket {ticket.id}: {e}")


def sendHtmlMail(view,subject,to_email,from_email=None,context={}):
    html_content = render_to_string(view,context)
    # Generate a plain text version of the email (fallback for clients that do not support HTML)
    text_content = strip_tags(html_content)
    if from_email is None:
        from_email = settings.EMAIL_HOST_USER

    email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    # Attach the HTML version
    email.attach_alternative(html_content, "text/html")
    # Send the email
    email.send()
    print("HTML email sent successfully!")