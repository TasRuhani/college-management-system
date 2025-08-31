from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q, F, FloatField, Case, When
from django.core.cache import cache
from .models import Student, Faculty, Course, Assessment, Attendance, Result
from .forms import LoginForm, AssignmentForm

@login_required
def role_selection_view(request):
    if request.user.is_staff and hasattr(request.user, 'faculty'):
        return render(request, 'role_selection.html')
    return redirect('login')

def login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'faculty') and request.user.is_superuser:
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
            if hasattr(user, 'faculty') and user.is_superuser:
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
    student = get_object_or_404(
        Student.objects.select_related('user', 'dept').prefetch_related('enrolled_courses__faculty', 'enrolled_courses__dept'),
        pk=request.user.pk
    )
    
    courses = student.enrolled_courses.all()

    attendance_data = []
    for course in courses:
        attendance_data.append({
            'course': course,
            'percentage': student.get_attendance_percentage(course)
        })

    assessments_with_results = []
    all_assessments = Assessment.objects.filter(course__in=courses).prefetch_related('result_set').order_by('course')
    
    for assessment in all_assessments:
        result = next((r for r in assessment.result_set.all() if r.student_id == student.user_id), None)
        assessments_with_results.append({
            'assessment': assessment,
            'result': result
        })

    context = {
        'student': student,
        'assessments_with_results': assessments_with_results,
        'attendance_data': attendance_data, 
    }
    return render(request, 'student_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    teacher = get_object_or_404(Faculty, pk=request.user.pk)
    courses = Course.objects.filter(faculty=teacher).select_related('dept', 'faculty')
    context = {
        'teacher': teacher,
        'courses': courses,
    }
    return render(request, 'teacher_dashboard.html', context)

@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, course_id=course_id)
    
    student_list_cache_key = f'course_{course_id}_student_list'
    students_in_course = cache.get(student_list_cache_key)

    if not students_in_course:
        students_in_course = course.enrolled_students.all()
        cache.set(student_list_cache_key, students_in_course, 3600) #1hr

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
        cache.delete(f'course_{course_id}_attendance_summary')
        return redirect('course_detail', course_id=course.course_id)

    view_date_str = request.GET.get('date', timezone.now().strftime("%Y-%m-%d"))
    view_date = timezone.datetime.strptime(view_date_str, "%Y-%m-%d").date()

    present_student_ids = set(Attendance.objects.filter(
        course=course, date=view_date, status=True
    ).values_list('student_id', flat=True))

    students_with_attendance = students_in_course.annotate(
        total_classes=Count('attendance', filter=Q(attendance__course=course)),
        present_classes=Count('attendance', filter=Q(attendance__course=course, attendance__status=True))
    ).annotate(
        attendance_percentage=Case(
            When(total_classes=0, then=0.0),
            default=(F('present_classes') * 100.0 / F('total_classes')),
            output_field=FloatField()
        )
    )

    student_data = []
    for student in students_with_attendance:
        student_data.append({
            'student': student,
            'attendance_percentage': student.attendance_percentage, 
            'is_present_today': student.pk in present_student_ids
        })
    
    cache_key = f'course_{course_id}_attendance_summary'
    attendance_summary = cache.get(cache_key)
    if not attendance_summary:
        attendance_summary = Attendance.objects.filter(course=course) \
            .values('date') \
            .annotate(present_count=Count('pk', filter=Q(status=True))) \
            .order_by('-date')
        cache.set(cache_key, attendance_summary, 900) # Cache for 15 minutes

    context = {
        'course': course,
        'student_data': student_data,
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
            assessment.save()
            return redirect('course_detail', course_id=course.course_id)
    else:
        form = AssignmentForm()
    return render(request, 'add_assignment.html', {'form': form, 'course': course})

@login_required
def assessment_detail_view(request, assessment_id):
    assessment = get_object_or_404(Assessment.objects.select_related('course'), assessment_id=assessment_id)
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

    results = Result.objects.filter(assessment=assessment, student__in=students)
    results_map = {result.student_id: result.marks for result in results}

    student_results = []
    for student in students:
        student_results.append({
            'student': student,
            'marks': results_map.get(student.user_id) 
        })

    context = {
        'assessment': assessment,
        'student_results': student_results,
    }
    return render(request, 'assessment_detail.html', context)