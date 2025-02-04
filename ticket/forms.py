from django import forms
from .models import Ticket

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