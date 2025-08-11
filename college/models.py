from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# for both Students and Faculty
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ("student", "Student"),
        ("faculty", "Faculty"),
        ("admin", "Admin"),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default="student")

class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.dept_name

class Faculty(models.Model):
    TITLE_CHOICES = (
        ('assistant_prof', 'Assistant Professor'),
        ('associate_prof', 'Associate Professor'),
        ('hod', 'HOD of Department'),
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

class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=100)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.course_name

class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    roll_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.IntegerField()
    enrolled_courses = models.ManyToManyField(Course, through='Enrollment', related_name='enrolled_students')

    def __str__(self):
        return self.name

class Enrollment(models.Model):
    enrollment_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"

class Attendance(models.Model):
    attendance_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.BooleanField(default=False) # true: present, false: absent

    def __str__(self):
        return f"{self.student} - {self.course} on {self.date}"

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

class Result(models.Model):
    result_id = models.AutoField(primary_key=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    marks = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ('assessment', 'student')

    def __str__(self):
        return f"Result for {self.student} in {self.assessment}"