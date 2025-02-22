import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr
from django.conf import settings
from ticket.models import Ticket, CustomUser, Student

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

def fetch_and_create_tickets():
    # These settings should be defined in your settings.py
    IMAP_HOST = "imap.gmail.com"
    IMAP_PORT = 993
    USERNAME = settings.EMAIL_HOST_USER      # e.g. "testingteamsk@gmail.com"
    PASSWORD = settings.EMAIL_HOST_PASSWORD  # your App Password

    try:
        print("Fetching emails...")
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(USERNAME, PASSWORD)
        mail.select("INBOX")
        # Use 'UNSEEN' to get only new messages
        status, message_numbers = mail.search(None, 'UNSEEN')
        print(status, message_numbers)
        if status != "OK":
            print("No new messages found!")
            return

        print(f"Found {len(message_numbers[0].split())} new messages")
        for num in message_numbers[0].split():
            status, data = mail.fetch(num, '(RFC822)')
            if status != "OK":
                print(f"Failed to fetch message {num}")
                continue

            raw_email = data[0][1]

            msg = email.message_from_bytes(raw_email)

            # Now that msg is defined, decode the fields.
            subject = decode_mime_words(msg.get("Subject"))
            body = get_body(msg)

            raw_from = msg.get("From")
            _, from_email = parseaddr(raw_from)

            student = Student.objects.filter(user__email=from_email).first()
            if not student:
                print(f"Skipping email from {from_email} (not a student)")
                continue

            print(f"Processing email from: {from_email}")


            msg_id = msg.get("Message-ID")
            if not msg_id:
                msg_id = f"{msg.get('From')}_{msg.get('Date')}"

            if Ticket.objects.filter(message_id=msg_id).exists():
                continue

            Ticket.objects.create(
                subject=subject or "No Subject",
                student=student,
                description=body,
                message_id=msg_id,
            )
            print(f"Created ticket from email: {subject}")

            # Mark the email as seen
            mail.store(num, '+FLAGS', '\\Seen')

        mail.logout()
    except Exception as e:
        print("Error fetching emails:", e)
