from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings  
from django.utils.timezone import now, timedelta
from datetime import timedelta 
import uuid

DEPT_CHOICES = settings.DEPT_CHOICES


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    )
    first_name = models.CharField(max_length=150, blank=False)  
    last_name = models.CharField(max_length=150, blank=False)   
    email = models.EmailField(unique=True, blank=False)
    preferred_name = models.CharField(max_length=150, blank=True, null=True)
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_email_verified = models.BooleanField(default=False)
    
    remember_token = models.CharField(max_length=64, blank=True, null=True, unique=True)
    remember_token_expiry = models.DateTimeField(blank=True, null=True)

    def generate_remember_token(self):
        """Generate a unique password reset token and store it."""
        import secrets
        self.remember_token = secrets.token_urlsafe(32)  # Secure token
        self.remember_token_expiry = now() + timedelta(hours=1)  # Expire in 1 hour
        self.save()
        return self.remember_token

    def is_remember_token_valid(self, token):
        """Validate the token against the stored token and check expiry."""
        return self.remember_token == token and self.remember_token_expiry and now() < self.remember_token_expiry

    def clear_remember_token(self):
        """Clear the reset token after use."""
        self.remember_token = None
        self.remember_token_expiry = None
        self.save()

    def save(self, *args, **kwargs):
        if not self.preferred_name:
            self.preferred_name = self.first_name
        super().save(*args, **kwargs)


class Staff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    role = models.CharField(max_length=50)
    date_joined = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='media/profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    def get_department_display(self):
        """Map the department choice to a human-readable format"""
        DEPT_DICT = dict(DEPT_CHOICES)  
        return DEPT_DICT.get(self.department, "Not Assigned")  

class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    program = models.CharField(max_length=100)
    year_of_study = models.IntegerField(default=1)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.program}"

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
    ]
    DEPT_CHOICES = [
        ('arts_humanities', 'Arts & Humanities'),
        ('business', 'Business'),
        ('dentistry', 'Dentistry, Oral & Craniofacial Sciences'),
        ('law', 'Law'),
        ('life_sciences_medicine', 'Life Sciences & Medicine'),
        ('natural_mathematical_engineering', 'Natural, Mathematical & Engineering Sciences'),
        ('nursing', 'Nursing, Midwifery & Palliative Care'),
        ('psychiatry', 'Psychiatry, Psychology & Neuroscience'), 
        ('social_science', 'Social Science & Public Policy'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
    ]
    RATING_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]

    subject = models.CharField(max_length=200)
    description = models.TextField()
    department = models.CharField(max_length=50, choices=DEPT_CHOICES, null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, null=True, blank=True)
   
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submitted_tickets', null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    assigned_staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    date_submitted = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_closed = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_tickets')
    expiration_date = models.DateTimeField(default=now() + timedelta(days=30))

    message_id = models.CharField(max_length=255, blank=True, null=True)
    ai_response = models.BooleanField(default=False)
    
    # Rating field - nullable because rating is only available after closure
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    rating_comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"

    
    def save(self, *args, **kwargs):

        """Auto-close tickets if expiration time has passed."""
        if self.status in ['open', 'pending'] and now() >= self.expiration_date:
            self.status = 'closed'
            self.date_closed = now()
            self.closed_by = self.assigned_staff if self.assigned_staff else None
        super().save(*args, **kwargs)

    admin_message = models.TextField(null=True, blank=True)

    @property
    def has_message(self):
        return bool(self.admin_message)
        
    class Meta:
        ordering = ['-date_submitted'] 

class StudentMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='student_messages')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class AdminMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='admin_messages')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class StaffMessage(models.Model):
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='staff_messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Staff message from {self.author} on {self.created_at}"


    class Meta:
        ordering = ['created_at']


class Announcement(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='announcements')
    department = models.CharField(max_length=50, choices=DEPT_CHOICES, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
