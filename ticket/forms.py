from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from ticket.models import CustomUser, Ticket

DEPT_CHOICES = [
    ('', 'Select Department'),
    ('arts_humanities', 'Arts & Humanities'),
    ('business', 'Business'),
    ('dentistry', 'Dentistry'),
    ('law', 'Law'),
    ('life_sciences_medicine', 'Life Sciences & Medicine'),
    ('natural_mathematical_engineering', 'Natural, Mathematical & Engineering Sciences'),
    ('nursing', 'Nursing'),
    ('psychiatry', 'Psychiatry'),
    ('social_science', 'Social Science')
]

class StaffUpdateProfileForm(forms.ModelForm):
    """Form for staff to update their profile information."""

    department = forms.ChoiceField(
        required=True, 
        choices=DEPT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    profile_picture = forms.ImageField(
        required=False, 
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'preferred_name', 'profile_picture']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Bootstrap styling        
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            
        self.fields['department'].initial = self.instance.staff.department
        self.fields['profile_picture'].initial = self.instance.staff.profile_picture

    def save(self, commit=True):
        """Save user and update the related Staff model."""
        user = super().save(commit=False)
        
    
        user.staff.department = self.cleaned_data['department']
        if self.cleaned_data.get('profile_picture'):
            user.staff.profile_picture = self.cleaned_data['profile_picture']
        if commit:
            user.staff.save()

        if commit:
            user.save()
        
        return user

class LogInForm(forms.Form):
    """Form enabling registered users to log in."""

    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())

    def get_user(self):
        """Returns authenticated user if possible."""

        user = None
        if self.is_valid():
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
        return user


class SignUpForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[('', 'Select Role')] + list(CustomUser.ROLE_CHOICES),
        required=True
    )
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    # Student specific fields
    department = forms.CharField(max_length=100, required=False)
    program = forms.CharField(max_length=100, required=False)
    year_of_study = forms.IntegerField(min_value=1, max_value=7, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].widget = forms.Select(choices=[
            ('', 'Select Department'),
            ('arts_humanities', 'Arts & Humanities'),
            ('business', 'Business'),
            ('dentistry', 'Dentistry'),
            ('law', 'Law'),
            ('life_sciences_medicine', 'Life Sciences & Medicine'),
            ('natural_mathematical_engineering', 'Natural, Mathematical & Engineering Sciences'),
            ('nursing', 'Nursing'),
            ('psychiatry', 'Psychiatry'),
            ('social_science', 'Social Science')
        ])

        # Initially hide student-specific fields
        for field in ['department', 'program', 'year_of_study']:
            self.fields[field].widget.attrs['class'] = 'student-field d-none'

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # Ensure password mismatch error is correctly raised
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "The two password fields didn't match.")

        # Validate required fields for students
        if role == 'student':
            if not cleaned_data.get('department'):
                self.add_error('department', 'This field is required for students.')
            if not cleaned_data.get('program'):
                self.add_error('program', 'This field is required for students.')
            if not cleaned_data.get('year_of_study'):
                self.add_error('year_of_study', 'This field is required for students.')

        return cleaned_data
  
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['subject', 'description', 'department']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of your query'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Please provide detailed information about your query',
                'rows': 5
            }),
            'department': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)

        self.fields['subject'].help_text = 'Enter a clear, brief title for your query'
        self.fields[
            'description'].help_text = 'Include all relevant details, dates, and any other information that might be helpful'

        for field in self.fields:
            self.fields[field].required = True

    def save(self, commit=True):
        ticket = super().save(commit=False)
        if self.student:
            ticket.student = self.student
        if commit:
            ticket.save()
        return ticket

