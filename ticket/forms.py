from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from ticket.models import CustomUser, Ticket


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
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists. Please log in.")
        return email
  
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
    
    #USE THIS AFTER Student MODEL IS MADE
    # def __init__(self, *args, **kwargs):
    #     self.student = kwargs.pop('student', None)
    #     super().__init__(*args, **kwargs)
        

    #     self.fields['subject'].help_text = 'Enter a clear, brief title for your query'
    #     self.fields['description'].help_text = 'Include all relevant details, dates, and any other information that might be helpful'
    #     #Should I make these tooltips instead?

    #     for field in self.fields:
    #         self.fields[field].required = True
    
    #THIS VERSION IS FOR TESTING - REAL VERSION ABOVE
    def __init__(self, *args, **kwargs):
      self.student = kwargs.pop('student', None) if 'student' in kwargs else None
      super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        ticket = super().save(commit=False)
        if self.student:
            ticket.student = self.student
        if commit:
            ticket.save()
        return ticket
