from django.contrib import admin
from .models import User, Department, Faculty, Course, Student, Enrollment, Attendance, Assessment, Result

# Register all the new models to be accessible in the admin panel
admin.site.register(User)
admin.site.register(Department)
admin.site.register(Faculty)
admin.site.register(Course)
admin.site.register(Student)
admin.site.register(Enrollment)
admin.site.register(Attendance)
admin.site.register(Assessment)
admin.site.register(Result)