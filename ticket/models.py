from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings  
from django.utils.timezone import now, timedelta
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

    def save(self, *args, **kwargs):
        if not self.preferred_name:
            self.preferred_name = self.first_name
        super().save(*args, **kwargs)


class Staff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    role = models.CharField(max_length=50)
    date_joined = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

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

    ai_response = models.BooleanField(default=False)

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"
    
    def save(self, *args, **kwargs):
        """Auto-close tickets if expiration time has passed."""
        if self.status in ['open', 'pending'] and now() >= self.expiration_date:
            self.status = 'closed'
            self.date_closed = now()
            self.closed_by = self.assigned_staff if self.assigned_staff else None
        super().save(*args, **kwargs)
    class Meta:
        ordering = ['-date_submitted'] 
class Message(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
