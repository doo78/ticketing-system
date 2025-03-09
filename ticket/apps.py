import atexit
import os
from django.apps import AppConfig
import datetime

class TicketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ticket'

    def ready(self):
        if os.environ.get('RUN_MAIN') != 'true':
            print(f"[{datetime.datetime.now()}] Skipping scheduler start in process {os.getpid()}")
            return

        from apscheduler.schedulers.background import BackgroundScheduler
        from django_apscheduler.jobstores import DjangoJobStore
        from ticket.email_utils import fetch_and_create_tickets, send_reminder_emails

        print(f"[{datetime.datetime.now()}] Starting scheduler in process {os.getpid()}")
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            fetch_and_create_tickets,
            trigger='interval',
            minutes=0.5,
            id='fetch_emails_job',
            name='Fetch new emails and create tickets',
            jobstore='default',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        scheduler.add_job(
            send_reminder_emails,
            trigger='interval',
            minutes=60,  # Run once hourly
            id='send_reminders_job',
            name='Send reminder emails for unanswered tickets',
            jobstore='default',
            replace_existing=True,
        )

        scheduler.start()
        print(f"[{datetime.datetime.now()}] Scheduler started in process {os.getpid()}")
        atexit.register(lambda: scheduler.shutdown())