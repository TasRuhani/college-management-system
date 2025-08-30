from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('course/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('course/<int:course_id>/add_assignment/', views.add_assignment_view, name='add_assignment'),
    path('assessment/<int:assessment_id>/', views.assessment_detail_view, name='assessment_detail'),
    path('select-role/', views.role_selection_view, name='select_role'),
    path('create-cache-table-_Gd8fN9s/', views.create_cache_table_view, name='create_cache_table'),
]