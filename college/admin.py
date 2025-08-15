import csv
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from .models import User, Department, Faculty, Course, Student, Enrollment, Attendance, Assessment, Result
from .forms import CsvImportForm

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_no', 'dept', 'semester')
    actions = ["import_from_csv"]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                
                for row in reader:
                    dept, _ = Department.objects.get_or_create(dept_name=row['dept_name'])
                    user, created = User.objects.get_or_create(
                        username=row['roll_no'],
                        defaults={'password': row['roll_no'], 'user_type': 'student'}
                    )
                    if created:
                        Student.objects.create(
                            user=user,
                            roll_no=row['roll_no'],
                            name=row['name'],
                            dept=dept,
                            semester=row['semester']
                        )
                
                self.message_user(request, "Your csv file has been imported")
                return redirect("..")
        
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_import.html", payload)
        
    def import_from_csv(self, request, queryset):
        return redirect("import-csv/")
    
    import_from_csv.short_description = "Import Students from CSV"

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('faculty_name', 'dept', 'title')
    actions = ["import_from_csv"]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                
                for row in reader:
                    dept, _ = Department.objects.get_or_create(dept_name=row['dept_name'])
                    user, created = User.objects.get_or_create(
                        username=row['username'],
                        defaults={'password': row['username'], 'user_type': 'faculty'}
                    )
                    if created:
                        Faculty.objects.create(
                            user=user,
                            faculty_name=row['faculty_name'],
                            dept=dept,
                            title=row['title']
                        )
                
                self.message_user(request, "Your csv file has been imported")
                return redirect("..")
        
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_import.html", payload)
        
    def import_from_csv(self, request, queryset):
        return redirect("import-csv/")
    
    import_from_csv.short_description = "Import Faculties from CSV"


admin.site.register(User)
admin.site.register(Department)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Attendance)
admin.site.register(Assessment)
admin.site.register(Result)