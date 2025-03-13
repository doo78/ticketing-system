from django.core.management.base import BaseCommand
from ticket.models import Ticket, Staff, Student, CustomUser 

class Command(BaseCommand):
    """Deletes all seeded data from the database."""

    help = "Deletes all seeded users, roles, and tickets."

    def handle(self, *args, **options):
        self.stdout.write("Starting the unseeding process...")

        Ticket.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("All tickets deleted."))

        Staff.objects.all().delete()
        Student.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("All staff and students deleted."))

        CustomUser.objects.exclude(is_superuser=True).delete()
        self.stdout.write(self.style.SUCCESS("All non-superuser users deleted."))

        self.stdout.write(self.style.SUCCESS("Database cleanup complete!"))