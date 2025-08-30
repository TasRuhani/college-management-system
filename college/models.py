from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# The User model is the foundation for both Students and Faculty
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ("student", "Student"),
        ("faculty", "Faculty"),
        ("admin", "Admin"),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default="student")

# 1. Department Model
class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.dept_name

# 2. Faculty Model
class Faculty(models.Model):
    TITLE_CHOICES = (
        ('assistant_prof', 'Assistant Professor'),
        ('associate_prof', 'Associate Professor'),
        ('hod', 'Head of Department'),
        ('non_teaching', 'Non-teaching Staff'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    faculty_name = models.CharField(max_length=100)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    title = models.CharField(max_length=20, choices=TITLE_CHOICES, default='assistant_prof')

    def __str__(self):
        return self.faculty_name
    
    class Meta:
        verbose_name_plural = "Faculties"

# 3. Course Model
class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=100)
    course_code = models.CharField(max_length=15, unique=True)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.course_name

# 4. Student Model
class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    roll_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.IntegerField()
    enrolled_courses = models.ManyToManyField(Course, through='Enrollment', related_name='enrolled_students')

    def __str__(self):
        return self.name
    
    def __str__(self):
        return self.name

    def get_attendance_percentage(self, course):
        """Calculates attendance percentage for a specific course."""
        total_classes = Attendance.objects.filter(student=self, course=course).count()
        if total_classes == 0:
            return 0 
        
        present_classes = Attendance.objects.filter(
            student=self, 
            course=course, 
            status=True
        ).count()
        
        return (present_classes / total_classes) * 100

    def get_overall_attendance_percentage(self):
        """Calculates the average attendance percentage across all enrolled courses."""
        percentages = []
        for course in self.enrolled_courses.all():
            percentages.append(self.get_attendance_percentage(course))
        
        if not percentages:
            return 0
            
        return sum(percentages) / len(percentages)

# 5. Enrollment (Junction Table for Student-Course)
class Enrollment(models.Model):
    enrollment_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"

# 6. Attendance Model
class Attendance(models.Model):
    attendance_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.BooleanField(default=False) # True for present, False for absent

    def __str__(self):
        return f"{self.student} - {self.course} on {self.date}"

# 7. Assessment Model
class Assessment(models.Model):
    ASSESSMENT_TYPE_CHOICES = (
        ('exam', 'Exam'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
    )
    assessment_id = models.AutoField(primary_key=True)
    assessment_name = models.CharField(max_length=100)
    assessment_full_marks = models.DecimalField(max_digits=5, decimal_places=2)
    type = models.CharField(max_length=20, choices=ASSESSMENT_TYPE_CHOICES)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.course}: {self.assessment_name} ({self.type})"

# 8. Result Model
class Result(models.Model):
    result_id = models.AutoField(primary_key=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    marks = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ('assessment', 'student')

    def __str__(self):
        return f"Result for {self.student} in {self.assessment}"