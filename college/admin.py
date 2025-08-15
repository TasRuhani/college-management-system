import csv
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, Faculty, Course, Student, Enrollment, Attendance, Assessment, Result
from .forms import CsvImportForm

# A Mixin for adding a generic "Export as CSV" action
class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response
    export_as_csv.short_description = "Export Selected as CSV"

# An inline view to show enrolled students on the Course page
class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    readonly_fields = ('student_name', 'student_roll_no', 'attendance_percentage')
    can_delete = False
    def student_name(self, instance):
        return instance.student.name
    def student_roll_no(self, instance):
        return instance.student.roll_no
    def attendance_percentage(self, instance):
        percentage = instance.student.get_attendance_percentage(instance.course)
        return f"{percentage:.2f}%"
    def has_add_permission(self, request, obj=None):
        return False

# Custom Admin Configurations for each model
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('course_name', 'course_code', 'dept', 'faculty')
    actions = ["import_from_csv", "export_as_csv"] # Added import action
    inlines = [EnrollmentInline]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path('import-csv/', self.import_csv)]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                
                for row in reader:
                    # Find the related Department
                    try:
                        department = Department.objects.get(dept_name=row['dept_name'])
                    except Department.DoesNotExist:
                        # Skip row if department doesn't exist, or create it
                        # For now, we'll skip it.
                        continue

                    # Find the related Faculty (if provided)
                    faculty = None
                    if row.get('faculty_username'):
                        try:
                            faculty_user = User.objects.get(username=row['faculty_username'])
                            faculty = Faculty.objects.get(user=faculty_user)
                        except (User.DoesNotExist, Faculty.DoesNotExist):
                            faculty = None

                    # Create the Course, avoiding duplicates based on course_code
                    Course.objects.get_or_create(
                        course_code=row['course_code'],
                        defaults={
                            'course_name': row['course_name'],
                            'dept': department,
                            'faculty': faculty
                        }
                    )
                
                self.message_user(request, "Your csv file has been imported")
                return redirect("..")
        
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_import.html", payload)
        
    def import_from_csv(self, request, queryset):
        return redirect("import-csv/")
    
    import_from_csv.short_description = "Import Courses from CSV"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('name', 'roll_no', 'dept', 'semester', 'attendance_percentage')
    ordering = ('name', 'roll_no')
    actions = ["import_from_csv", "export_as_csv"]

    def attendance_percentage(self, obj):
        return f"{obj.get_overall_attendance_percentage():.2f}%"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path('import-csv/', self.import_csv)]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                for row in reader:
                    username = row.get('username') or row['roll_no'] # Use username if present, else fallback to roll_no
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'password': row.get('password') or row['roll_no'],
                            'user_type': 'student'
                        }
                    )
                    if not Student.objects.filter(user=user).exists():
                        dept, _ = Department.objects.get_or_create(dept_name=row['dept_name'])
                        Student.objects.create(
                            user=user, roll_no=row['roll_no'], name=row['name'],
                            dept=dept, semester=row['semester']
                        )
                self.message_user(request, "CSV file has been processed.")
                return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_import.html", payload)

    def import_from_csv(self, request, queryset):
        return redirect("import-csv/")
    import_from_csv.short_description = "Import Students from CSV"

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('faculty_name', 'dept', 'title')
    actions = ["import_from_csv", "export_as_csv"]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path('import-csv/', self.import_csv)]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                for row in reader:
                    user, created = User.objects.get_or_create(
                        username=row['username'],
                        defaults={
                            'password': row.get('password') or row['username'],
                            'user_type': 'faculty'
                        }
                    )
                    if not Faculty.objects.filter(user=user).exists():
                        dept, _ = Department.objects.get_or_create(dept_name=row['dept_name'])
                        Faculty.objects.create(
                            user=user, faculty_name=row['faculty_name'],
                            dept=dept, title=row['title']
                        )
                self.message_user(request, "CSV file has been processed.")
                return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_import.html", payload)
    
    def import_from_csv(self, request, queryset):
        return redirect("import-csv/")
    import_from_csv.short_description = "Import Faculties from CSV"

@admin.register(User)
class CustomUserAdmin(UserAdmin, ExportCsvMixin):
    actions = ["export_as_csv", "import_from_csv"]
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('College Role', {'fields': ('user_type',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path('import-csv/', self.import_csv)]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                for row in reader:
                    # Read the staff_status from the CSV and convert it to a boolean
                    is_staff_value = row.get('is_staff', 'FALSE').lower() == 'true'
                    
                    # Use create_user to properly hash passwords
                    User.objects.create_user(
                        username=row['username'],
                        password=row['password'],
                        email=row['email'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        user_type=row['user_type'],
                        is_staff=is_staff_value # Pass the value here
                    )
                self.message_user(request, "Users have been imported from the CSV file.")
                return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_import.html", payload)

    def import_from_csv(self, request, queryset):
        return redirect("import-csv/")
    import_from_csv.short_description = "Import Users from CSV"

# Register other models with export functionality
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin, ExportCsvMixin):
    actions = ["export_as_csv"]

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('student', 'course', 'enrollment_date')
    actions = ["import_from_csv", "export_as_csv"] # Added import action

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path('import-csv/', self.import_csv)]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                
                for row in reader:
                    try:
                        # Find the student and course from the CSV data
                        student = Student.objects.get(roll_no=row['student_roll_no'])
                        course = Course.objects.get(course_code=row['course_code'])
                        
                        # Create the enrollment link if it doesn't already exist
                        Enrollment.objects.get_or_create(
                            student=student,
                            course=course
                        )
                    except (Student.DoesNotExist, Course.DoesNotExist):
                        # If a student or course is not found, just skip this row
                        continue
                
                self.message_user(request, "Your csv file has been imported")
                return redirect("..")
        
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_import.html", payload)
        
    def import_from_csv(self, request, queryset):
        return redirect("import-csv/")
    
    import_from_csv.short_description = "Import Enrollments from CSV"
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('student', 'student_roll_no', 'course', 'date', 'status')
    actions = ["export_as_csv"]
    def student_roll_no(self, obj):
        return obj.student.roll_no
    student_roll_no.short_description = 'Roll No'

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin, ExportCsvMixin):
    actions = ["export_as_csv"]

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin, ExportCsvMixin):
    actions = ["export_as_csv"]