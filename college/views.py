# college/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

# ↓↓ REMOVED 'News' FROM THE IMPORTS ↓↓
from .models import Student, Faculty, Course, Assessment, Attendance
from .forms import LoginForm, AttendanceForm, AssignmentForm

def login_view(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'student':
            return redirect('student_dashboard')
        elif request.user.user_type == 'faculty':
            return redirect('teacher_dashboard')
        else:
            return redirect('/admin/')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.user_type == 'student':
                return redirect('student_dashboard')
            elif user.user_type == 'faculty':
                return redirect('teacher_dashboard')
            else:
                return redirect('/admin/')

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def student_dashboard(request):
    # ↓↓ CORRECTED THIS QUERY ↓↓
    # Query by the primary key (pk) of the logged-in user
    student = get_object_or_404(Student, pk=request.user.pk)
    
    courses = student.enrolled_courses.all()
    assessments = Assessment.objects.filter(course__in=courses)
    context = {
        'student': student,
        'courses': courses,
        'assessments': assessments,
    }
    return render(request, 'student_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    # ↓↓ CORRECTED THIS QUERY ↓↓
    # Query by the primary key (pk) of the logged-in user
    teacher = get_object_or_404(Faculty, pk=request.user.pk)

    courses = Course.objects.filter(faculty=teacher)
    context = {
        'teacher': teacher,
        'courses': courses,
    }
    return render(request, 'teacher_dashboard.html', context)

@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, course_id=course_id)
    students = course.enrolled_students.all()
    assessments = Assessment.objects.filter(course=course)

    if request.method == 'POST':
        for student in students:
            is_present = request.POST.get(f'student_{student.student_id.id}') == 'on'
            Attendance.objects.update_or_create(
                student=student,
                course=course,
                date=timezone.now().date(),
                defaults={'status': is_present}
            )
        return redirect('course_detail', course_id=course.id)

    context = {
        'course': course,
        'students': students,
        'assessments': assessments,
    }
    return render(request, 'course_detail.html', context)

@login_required
def add_assignment_view(request, course_id):
    course = get_object_or_404(Course, course_id=course_id)
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.course = course
            assessment.type = 'assignment'
            assessment.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = AssignmentForm()

    return render(request, 'add_assignment.html', {'form': form, 'course': course})

# ↓↓ DELETED THE ENTIRE news_board FUNCTION ↓↓