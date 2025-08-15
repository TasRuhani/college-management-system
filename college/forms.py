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
        fields = ['assessment_name', 'type', 'assessment_full_marks']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_bound:
            self.fields['assessment_name'].initial = "New Assessment"
            self.fields['assessment_full_marks'].initial = 100


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

class MarksEntryForm(forms.Form):
    marks = forms.DecimalField(max_digits=5, decimal_places=2, required=True)