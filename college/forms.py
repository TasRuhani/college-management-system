# college/forms.py

from django import forms
# ↓↓ CORRECTED THE IMPORTS ↓↓
from .models import Attendance, Assessment

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['status']

# ↓↓ CORRECTED TO USE 'Assessment' MODEL ↓↓
class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assessment # Changed from Assignment
        # Use the fields from the Assessment model
        fields = ['assessment_name', 'assessment_full_marks']