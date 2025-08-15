from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from .models import Student, Faculty, Course, Assessment, Attendance
from .forms import LoginForm, AttendanceForm, AssignmentForm
from .models import Result
from .forms import MarksEntryForm

@login_required
def role_selection_view(request):
    if request.user.is_staff and hasattr(request.user, 'faculty'):
        return render(request, 'role_selection.html')
    return redirect('login')

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff and hasattr(request.user, 'faculty'):
            return redirect('select_role')
        elif request.user.user_type == 'faculty':
            return redirect('teacher_dashboard')
        elif request.user.user_type == 'student':
            return redirect('student_dashboard')
        else:
            return redirect('/admin/')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            if user.is_staff and hasattr(user, 'faculty'):
                return redirect('select_role')
            elif user.user_type == 'faculty':
                return redirect('teacher_dashboard')
            elif user.user_type == 'student':
                return redirect('student_dashboard')
            elif user.is_staff:
                return redirect('/admin/')
            else:
                return redirect('login')
        else:
            form.add_error(None, "Your username and password didn't match. Please try again.")

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def student_dashboard(request):
    student = get_object_or_404(Student, pk=request.user.pk)
    courses = student.enrolled_courses.all()
    
    assessments_with_results = []
    all_assessments = Assessment.objects.filter(course__in=courses).order_by('course')
    for assessment in all_assessments:
        result = Result.objects.filter(student=student, assessment=assessment).first()
        assessments_with_results.append({
            'assessment': assessment,
            'result': result
        })
    
    attendance_data = []
    for course in courses:
        percentage = student.get_attendance_percentage(course)
        attendance_data.append({'course': course, 'percentage': percentage})

    context = {
        'student': student,
        'courses': courses,
        'assessments_with_results': assessments_with_results,
        'attendance_data': attendance_data,
    }
    return render(request, 'student_dashboard.html', context)

@login_required
def teacher_dashboard(request):
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
    students_in_course = course.enrolled_students.all()
    assessments = Assessment.objects.filter(course=course)
    
    if request.method == 'POST':
        date_str = request.POST.get("attendance_date")
        attendance_date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
        for student in students_in_course:
            is_present = request.POST.get(f'student_{student.user.id}') == 'on'
            Attendance.objects.update_or_create(
                student=student,
                course=course,
                date=attendance_date,
                defaults={'status': is_present}
            )
        return redirect('course_detail', course_id=course.course_id)

    view_date_str = request.GET.get('date', timezone.now().strftime("%Y-%m-%d"))
    view_date = timezone.datetime.strptime(view_date_str, "%Y-%m-%d").date()

    present_student_ids = Attendance.objects.filter(
        course=course, date=view_date, status=True
    ).values_list('student__user__id', flat=True)

    student_data = []
    for student in students_in_course:
        student_data.append({
            'student': student,
            'attendance_percentage': student.get_attendance_percentage(course),
            'is_present_today': student.user.id in present_student_ids
        })

    attendance_summary = Attendance.objects.filter(course=course) \
        .values('date') \
        .annotate(present_count=Count('pk', filter=Q(status=True))) \
        .order_by('-date')

    context = {
        'course': course,
        'student_data': student_data,
        'students': students_in_course,
        'assessments': assessments,
        'view_date': view_date,
        'attendance_summary': attendance_summary,
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
            return redirect('course_detail', course_id=course.course_id)
    else:
        form = AssignmentForm()

    return render(request, 'add_assignment.html', {'form': form, 'course': course})

@login_required
def assessment_detail_view(request, assessment_id):
    assessment = get_object_or_404(Assessment, assessment_id=assessment_id)
    students = assessment.course.enrolled_students.all()

    if request.method == 'POST':
        for student in students:
            marks = request.POST.get(f'marks_{student.user.id}')
            if marks: 
                Result.objects.update_or_create(
                    student=student,
                    assessment=assessment,
                    defaults={'marks': marks}
                )
        return redirect('assessment_detail', assessment_id=assessment.assessment_id)

    student_results = []
    for student in students:
        result = Result.objects.filter(student=student, assessment=assessment).first()
        student_results.append({
            'student': student,
            'marks': result.marks if result else None
        })

    context = {
        'assessment': assessment,
        'student_results': student_results,
    }
    return render(request, 'assessment_detail.html', context)