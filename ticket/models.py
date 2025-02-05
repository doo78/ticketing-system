from django.db import models
from django.contrib.auth.models import User , AbstractUser
from django.conf import settings  


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

class Staff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    role = models.CharField(max_length=50)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
    ]

    subject = models.CharField(max_length=200)
    description = models.TextField()
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    date_submitted = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_closed = models.DateField(blank=True, null=True)
    assigned_staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    closed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_tickets')

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"