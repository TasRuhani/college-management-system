from django import forms
from .models import Attendance, Assessment

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['status']

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assessment 
        fields = ['assessment_name', 'assessment_full_marks']

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()