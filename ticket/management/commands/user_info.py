from django.core.management.base import BaseCommand
from ticket.models import CustomUser

class Command(BaseCommand):
    """Displays all users with their roles and default passwords"""

    help = "Lists all users with their roles and password."

    def handle(self, *args, **options):
        users = CustomUser.objects.all()

        if not users.exists():
            self.stdout.write(self.style.WARNING("No users found in the database."))
            return

        self.stdout.write(self.style.SUCCESS("Listing all users:\n"))

        for user in users:
            self.stdout.write(f"Username: {user.username}, Role: {user.role}, Password: password123")