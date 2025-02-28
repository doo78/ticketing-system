import random
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from faker import Faker
from ticket.models import CustomUser, Staff, Student, Ticket
from django.utils.timezone import now, timedelta
from django.conf import settings

DEPT_CHOICES = settings.DEPT_CHOICES

fake = Faker()

# User Roles
ROLE_ADMIN = "admin"
ROLE_STAFF = "staff"
ROLE_STUDENT = "student"

# Fixed Users
DEFAULT_USERS = [
    {
        "username": "admin_user",
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "role": ROLE_ADMIN,
    },
    {
        "username": "staff_user",
        "email": "staff@example.com",
        "first_name": "Staff",
        "last_name": "User",
        "role": ROLE_STAFF,
    },
    {
        "username": "student_user",
        "email": "student@example.com",
        "first_name": "Student",
        "last_name": "User",
        "role": ROLE_STUDENT,
    },
]

class Command(BaseCommand):
    """Seed the database with roles, users, and tickets"""

    USER_COUNT = 50  # Number of random users
    TICKET_COUNT = 100  # Number of tickets to generate

    help = "Seeds the database with sample users, roles, and tickets"

    def handle(self, *args, **options):
        self.stdout.write("Starting the seeding process...")

        self.create_fixed_users()
        self.create_random_users()
        self.create_tickets()

        self.stdout.write(self.style.SUCCESS("Database seeding complete!"))

    def create_fixed_users(self):
        """Create predefined admin, staff, and student users"""
        for user_data in DEFAULT_USERS:
            self.create_user(user_data)
        self.stdout.write(self.style.SUCCESS("Fixed users created."))

    def create_random_users(self):
        """Generate random users with different roles"""
        for _ in range(self.USER_COUNT):
            role = random.choice([ROLE_STAFF, ROLE_STUDENT])  
            self.create_user({
                "username": fake.user_name(),
                "email": fake.email(),
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "role": role
            })
        self.stdout.write(self.style.SUCCESS(f"{self.USER_COUNT} random users created."))

    def create_user(self, data):
        """Helper function to create users"""
        user, created = CustomUser.objects.get_or_create(
            username=data["username"],
            defaults={
                "email": data["email"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "password": "password123",
                "role": data["role"],
            },
        )
        
        valid_departments = [choice[0] for choice in DEPT_CHOICES if choice[0]]

        if created:
            if data["role"] == ROLE_STAFF:
                Staff.objects.create(user=user, department=random.choice(valid_departments) if valid_departments else "", role="Support Staff")
            elif data["role"] == ROLE_STUDENT:
                Student.objects.create(user=user, department=random.choice(valid_departments) if valid_departments else "", program=fake.job(), year_of_study=random.randint(1, 4))

            user.set_password("password123")  
            user.save()
            self.stdout.write(self.style.SUCCESS(f"User created: {user.username} ({data['role']})"))
            
    def create_tickets(self):
        """Generate sample tickets"""
        students = Student.objects.all() 
        staff = Staff.objects.all()

        if not students.exists() or not staff.exists():
            self.stdout.write(self.style.ERROR("No students or staff available for ticket creation!"))
            return

        for _ in range(self.TICKET_COUNT):
            student = random.choice(students)
            status = random.choice(["open", "pending", "closed"])

            # Ensures open tickets aren't assigned staff
            assigned_staff = random.choice(staff) if status in ["pending", "closed"] else None
            
            date_submitted = now() - timedelta(days=random.randint(1, 30))  

            date_closed = date_submitted + timedelta(days=random.randint(1, 10)) if status == "closed" else None

            Ticket.objects.create(
                subject=fake.sentence(),
                description=fake.paragraph(),
                student=student,  
                assigned_staff=assigned_staff,
                status=status,
                priority=random.choice(["low", "normal", "urgent"]),
                date_submitted=date_submitted,
                date_closed=date_closed,
                department=random.choice(DEPT_CHOICES)[0],
            )

        self.stdout.write(self.style.SUCCESS(f"{self.TICKET_COUNT} tickets generated."))