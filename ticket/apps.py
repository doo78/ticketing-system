import atexit
import os
from django.apps import AppConfig

class TicketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ticket'

    def ready(self):
        # Only run in the main process.
        if os.environ.get('RUN_MAIN') != 'true':
            return

        from apscheduler.schedulers.background import BackgroundScheduler
        from django_apscheduler.jobstores import DjangoJobStore
        from ticket.email_utils import fetch_and_create_tickets

        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # Add the job and automatically replace an existing one with the same ID.
        scheduler.add_job(
            fetch_and_create_tickets,
            trigger='interval',
            minutes=0.1,  # Adjust as needed
            id='fetch_emails_job',  # Unique job id
            name='Fetch new emails and create tickets',
            jobstore='default',
            replace_existing=True,
        )

        scheduler.start()
        print("Scheduler started.")
        atexit.register(lambda: scheduler.shutdown())
