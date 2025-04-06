from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm,UserChangeForm
from ticket.models import CustomUser, Ticket, Department, Student, Staff


class DepartmentForm(forms.ModelForm):
    name=  forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter department name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter e-mail for a department'
        })
    )

    password = forms.CharField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            "type": "password",
            'placeholder': 'Enter email password'
        })
    )
    class Meta:
        model = Department
        fields = ['id','name',"email","password"]


class StaffUpdateProfileForm(forms.ModelForm):
    """
    For staff to update their profile information
    """
    department = forms.ChoiceField(
        required=True,
        # choices=Department.get_all_departments_list(),
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
        self.fields['department'].choices = Department.get_all_departments_list()
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        self.fields['department'].initial = self.instance.staff.department.id
        self.fields['profile_picture'].initial = self.instance.staff.profile_picture

    def save(self, commit=True):
        """Save user and update the related Staff model."""
        user = super().save(commit=False)
        department_id = self.cleaned_data.get('department')  # Get the selected ID

        # Convert department ID back to instance for saving related models if needed
        if department_id:
            try:
                self.cleaned_data['department_instance'] = Department.objects.get(pk=department_id)
            except Department.DoesNotExist:
                self.add_error('department', 'Invalid department selected.')
                self.cleaned_data['department_instance'] = None  # Ensure it's None if invalid
        else:
            self.cleaned_data['department_instance'] = None
        user.staff.department = self.cleaned_data['department_instance']
        if self.cleaned_data.get('profile_picture'):
            user.staff.profile_picture = self.cleaned_data['profile_picture']

        if commit:
            user.staff.save()

        if commit:
            user.save()

        return user


class AdminUpdateProfileForm(forms.ModelForm):
    """
    For staff to update their profile information
    """
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'preferred_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        """Save user and update the related Staff model."""
        user = super().save(commit=False)

        if commit:
            user.save()

        return user

class LogInForm(forms.Form):
    """
    Enables registered users to log in
    """

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
    """
    For signing up
    """
    # role = forms.ChoiceField(
    #     choices=[('', 'Select Role')] + list(CustomUser.ROLE_CHOICES),
    #     required=True
    # )
    role = forms.ChoiceField(
        choices=[('', 'Select Role')] + [choice for choice in CustomUser.ROLE_CHOICES if choice[0] != 'admin'],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    department = forms.CharField(max_length=100, required=False)
    program = forms.CharField(max_length=100, required=False)
    year_of_study = forms.IntegerField(min_value=1, max_value=7, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].choices = Department.get_all_departments_list()
        self.fields['department'].widget = forms.Select(choices=Department.get_all_departments_list())

        for field in ['department', 'program', 'year_of_study']:
            self.fields[field].widget.attrs['class'] = 'student-field d-none'

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "The two password fields didn't match.")

        if role == 'student':
            if not cleaned_data.get('department'):
                self.add_error('department', 'This field is required for students.')
            else:
                cleaned_data['department'] = Department.objects.get(pk=cleaned_data.get('department'))
            if not cleaned_data.get('program'):
                self.add_error('program', 'This field is required for students.')
            if not cleaned_data.get('year_of_study'):
                self.add_error('year_of_study', 'This field is required for students.')

        return cleaned_data

class EditAccountForm(UserChangeForm):
    """
    For the admin to edit accounts
    """
    role = forms.ChoiceField(
        choices=[('', 'Select Role')] + list(CustomUser.ROLE_CHOICES),
        required=True
    )
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    department = forms.ChoiceField(required=False)
    program = forms.CharField(max_length=100, required=False)
    year_of_study = forms.IntegerField(min_value=1, max_value=7, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].choices = Department.get_all_departments_list()

        # Set initial value for department if editing a student/staff
        if self.instance.pk:  # Check if instance exists (i.e., editing)
            if hasattr(self.instance, 'student') and self.instance.student.department:
                self.fields['department'].initial = self.instance.student.department.id
            elif hasattr(self.instance, 'staff') and self.instance.staff.department:
                self.fields['department'].initial = self.instance.staff.department.id

        # Apply form-control class to all fields
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
                field.widget.attrs['class'] = field.widget.attrs['class'].replace('student-field d-none',
                                                                                  '').strip()  # Avoid duplicating classes

        for field in ['department', 'program', 'year_of_study']:
            self.fields[field].widget.attrs['class'] = 'student-field d-none'

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')




        if password1 and password2 and password1 != password2:
            self.add_error('password2', "The two password fields didn't match.")

        if role == 'student':
            if not cleaned_data.get('department'):
                self.add_error('department', 'This field is required for students.')
            if not cleaned_data.get('program'):
                self.add_error('program', 'This field is required for students.')
            if not cleaned_data.get('year_of_study'):
                self.add_error('year_of_study', 'This field is required for students.')
        elif role == 'staff':
            if not cleaned_data.get('department'):  # Check the ID selected
                self.add_error('department', 'This field is required for staff.')

        department_id = cleaned_data.get('department')  # Get the selected ID

        # Convert department ID back to instance for saving related models if needed
        if department_id:
            try:
                cleaned_data['department_instance'] = Department.objects.get(pk=department_id)
            except Department.DoesNotExist:
                self.add_error('department', 'Invalid department selected.')
                cleaned_data['department_instance'] = None  # Ensure it's None if invalid
        else:
            cleaned_data['department_instance'] = None
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)  # Get user instance without committing yet

        department_instance = self.cleaned_data.get('department_instance')

        if commit:
            user.save()

        if user.role == 'student':
            student_defaults = {
                'department': department_instance,
                'program': self.cleaned_data.get('program', 'Undeclared'),
                'year_of_study': self.cleaned_data.get('year_of_study', 1)
            }
            student_profile, created = Student.objects.update_or_create(
                user=user, defaults=student_defaults
            )
            Staff.objects.filter(user=user).delete()
        elif user.role == 'staff':
            staff_defaults = {
                'department': department_instance,
            }
            staff_profile, created = Staff.objects.update_or_create(
                user=user, defaults=staff_defaults
            )
            Student.objects.filter(user=user).delete()
        elif user.role == 'admin':

            Student.objects.filter(user=user).delete()
            Staff.objects.filter(user=user).delete()
        return user

class TicketForm(forms.ModelForm):
    """
    For a student to create a ticket
    """
    department = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Ticket
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of your query'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Please provide detailed information about your query',
                'rows': 5
            })
        }

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        self.fields['department'].choices = Department.get_all_departments_list()
        if self.student:
            self.fields['department'].initial = self.student.department
        # Use the same department choices as defined in the Ticket model
        self.fields['department'].choices = Department.get_all_departments_list()
        self.fields['subject'].help_text = 'Enter a clear, brief title for your query'
        self.fields['description'].help_text = 'Include all relevant details, dates, and any other information that might be helpful'
        self.fields['department'].help_text = 'Select the department related to your query'

        for field in self.fields:
            self.fields[field].required = True

    def save(self, commit=True):
        ticket = super().save(commit=False)
        if self.student:
            ticket.student = self.student
            ticket.status = 'open'
        department_id = self.cleaned_data.get('department')
        if department_id:
            try:
                ticket.department = Department.objects.get(pk=department_id)  # Assign the instance
            except Department.DoesNotExist:
                ticket.department = None  # Or raise an error
        if commit:
            ticket.save()
        return ticket

class RatingForm(forms.ModelForm):
    """
    For students to rate their ticket experience after closure
    """
    class Meta:
        model = Ticket
        fields = ['rating', 'rating_comment']
        widgets = {
            'rating': forms.RadioSelect(),
            'rating_comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Share your thoughts about the support you received...'}),
        }
        labels = {
            'rating': 'How would you rate your experience?',
            'rating_comment': 'Comments (optional)',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating_comment'].required = False
        
class AdminUpdateForm(forms.ModelForm):
    """
    For admins to update their accounts
    """
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']

