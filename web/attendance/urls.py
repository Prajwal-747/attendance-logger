from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="attendance/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("classroom/create/", views.create_classroom, name="create_classroom"),
    path(
        "classroom/<int:classroom_id>/",
        views.classroom_detail,
        name="classroom_detail",
    ),
    path(
        "classroom/<int:classroom_id>/student/add/",
        views.add_student,
        name="add_student",
    ),
    path(
        "classroom/<int:classroom_id>/student/<int:student_id>/edit/",
        views.edit_student,
        name="edit_student",
    ),
    path(
        "classroom/<int:classroom_id>/student/<int:student_id>/delete/",
        views.delete_student,
        name="delete_student",
    ),
    path(
        "timetable/<int:timetable_entry_id>/attendance/",
        views.mark_attendance,
        name="mark_attendance",
    ),
    path(
        "timetable/<int:timetable_entry_id>/report/",
        views.daily_report,
        name="daily_report",
    ),
    path(
        "classroom/<int:classroom_id>/assign-subject/",
        views.assign_subject,
        name="assign_subject",
    ),
    path(
        "classroom/<int:classroom_id>/assign-class-teacher/",
        views.assign_class_teacher,
        name="assign_class_teacher",
    ),
    path(
        "classroom/<int:classroom_id>/timetable/",
        views.manage_timetable,
        name="manage_timetable",
    ),
    path(
        "teacher/timetable/",
        views.teacher_timetable,
        name="teacher_timetable",
    ),
    path(
        "classroom/<int:classroom_id>/report/",
        views.classroom_report,
        name="classroom_report",
    ),
    path(
        "student/<int:student_id>/report/",
        views.student_report,
        name="student_report",
    ),
    path(
        "teacher/<int:teacher_id>/report/",
        views.teacher_report,
        name="teacher_report",
    ),
]
