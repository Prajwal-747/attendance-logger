from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from .models import (
    User,
    Classroom,
    Subject,
    SubjectAssignment,
    TimetableEntry,
    AttendanceSession,
    Student,
    Attendance,
)
import secrets
import string
from django.contrib import messages
from datetime import date
from django.db import transaction
from django.urls import reverse
from django.core.exceptions import ValidationError


def get_accessible_classrooms(user):
    if user.role == User.Role.ADMIN:
        return Classroom.objects.all()

    if user.role == User.Role.TEACHER:
        return Classroom.objects.filter(
            Q(class_teacher=user) | Q(subject_assignments__teacher=user)
        ).distinct()

    return Classroom.objects.none()


def can_manage_classroom(user, classroom):
    return user.role == User.Role.ADMIN or (
        user.role == User.Role.TEACHER and classroom.class_teacher_id == user.id
    )


@login_required
def dashboard(request):
    classrooms = get_accessible_classrooms(request.user)

    return render(
        request,
        "attendance/dashboard.html",
        {
            "classrooms": classrooms,
            "user_role": request.user.role,
        },
    )


def generate_class_code():
    characters = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(characters) for _ in range(8))


@login_required
def create_classroom(request):
    if request.user.role != User.Role.ADMIN:
        messages.error(request, "Only the college admin can create classrooms.")
        return redirect("dashboard")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if name:
            Classroom.objects.create(
                name=name,
                code=generate_class_code(),
                class_teacher=None,
            )

            messages.success(request, "Classroom created successfully.")

        else:
            messages.error(request, "Please enter a classroom name.")

        return redirect("dashboard")

    return render(request, "attendance/create_classroom.html")


@login_required
def classroom_detail(request, classroom_id):
    classroom = get_object_or_404(
        get_accessible_classrooms(request.user),
        id=classroom_id,
    )

    students = classroom.students.order_by("roll_no")

    return render(
        request,
        "attendance/classroom_detail.html",
        {
            "classroom": classroom,
            "students": students,
            "can_manage": can_manage_classroom(request.user, classroom),
        },
    )


@login_required
def assign_subject(request, classroom_id):
    classroom = get_object_or_404(
        Classroom,
        id=classroom_id,
    )

    if not can_manage_classroom(request.user, classroom):
        messages.error(request, "You don't have permission to manage assignments.")
        return redirect("classroom_detail", classroom_id=classroom.id)

    if request.method == "POST":
        subject_name = request.POST.get("subject", "").strip()
        teacher_id = request.POST.get("teacher", "").strip()

        teacher = (
            get_object_or_404(
                User,
                id=teacher_id,
                role=User.Role.TEACHER,
            )
            if teacher_id.isdigit()
            else None
        )

        if not subject_name or teacher is None:
            messages.error(request, "Please enter a subject and select a teacher.")

        else:
            subject, _ = Subject.objects.get_or_create(name=subject_name)

            if SubjectAssignment.objects.filter(
                classroom=classroom,
                subject=subject,
            ).exists():
                messages.error(
                    request, "This subject is already assigned to this classroom."
                )

            else:
                SubjectAssignment.objects.create(
                    classroom=classroom,
                    subject=subject,
                    teacher=teacher,
                )
                messages.success(request, "Subject assigned successfully.")

        return redirect("classroom_detail", classroom_id=classroom.id)

    return render(
        request,
        "attendance/assign_subject.html",
        {
            "classroom": classroom,
            "teachers": User.objects.filter(role=User.Role.TEACHER).order_by(
                "username"
            ),
        },
    )


@login_required
def assign_class_teacher(request, classroom_id):
    if request.user.role != User.Role.ADMIN:
        messages.error(request, "Only the college admin can assign class teachers.")
        return redirect("dashboard")

    classroom = get_object_or_404(Classroom, id=classroom_id)

    teachers = (
        User.objects.filter(
            role=User.Role.TEACHER,
            subject_assignments__classroom=classroom,
        )
        .distinct()
        .order_by("username")
    )

    if request.method == "POST":
        teacher_id = request.POST.get("teacher", "").strip()

        teacher = teachers.filter(id=teacher_id).first()

        if teacher is None:
            messages.error(
                request,
                "Please select a teacher assigned to this classroom.",
            )
        else:
            classroom.class_teacher = teacher
            classroom.save()

            messages.success(request, "Class teacher assigned successfully.")

        return redirect("classroom_detail", classroom_id=classroom.id)

    return render(
        request,
        "attendance/assign_class_teacher.html",
        {
            "classroom": classroom,
            "teachers": teachers,
        },
    )


@login_required
def manage_timetable(request, classroom_id):
    classroom = get_object_or_404(
        get_accessible_classrooms(request.user),
        id=classroom_id,
    )

    if not can_manage_classroom(request.user, classroom):
        messages.error(
            request,
            "You don't have permission to manage this timetable.",
        )
        return redirect("classroom_detail", classroom_id=classroom.id)

    assignments = classroom.subject_assignments.select_related(
        "subject",
        "teacher",
    ).order_by("subject__name")

    if request.method == "POST":
        assignment_id = request.POST.get("assignment")
        weekday = request.POST.get("weekday")
        period = request.POST.get("period")

        assignment = assignments.filter(id=assignment_id).first()

        valid_weekdays = [choice[0] for choice in TimetableEntry.Weekday.choices]

        if (
            assignment is None
            or weekday not in valid_weekdays
            or not period
            or not period.isdigit()
            or not 1 <= int(period) <= 6
        ):
            messages.error(request, "Please enter valid timetable details.")
            return redirect("manage_timetable", classroom_id=classroom.id)

        entry = TimetableEntry(
            assignment=assignment,
            weekday=weekday,
            period=int(period),
        )

        try:
            entry.full_clean()
            entry.save()
            messages.success(request, "Timetable period added successfully.")

        except ValidationError as error:
            messages.error(request, error.messages[0])

        return redirect("manage_timetable", classroom_id=classroom.id)

    timetable_entries = (
        TimetableEntry.objects.filter(assignment__classroom=classroom)
        .select_related("assignment__subject", "assignment__teacher")
        .order_by("weekday", "period")
    )

    return render(
        request,
        "attendance/manage_timetable.html",
        {
            "classroom": classroom,
            "assignments": assignments,
            "timetable_entries": timetable_entries,
            "weekdays": TimetableEntry.Weekday.choices,
            "periods": range(1, 7),
        },
    )


@login_required
def teacher_timetable(request):
    if request.user.role != User.Role.TEACHER:
        messages.error(request, "This page is only for teachers.")
        return redirect("dashboard")

    timetable_entries = (
        TimetableEntry.objects.filter(assignment__teacher=request.user)
        .select_related(
            "assignment__classroom",
            "assignment__subject",
        )
        .order_by("weekday", "period")
    )

    return render(
        request,
        "attendance/teacher_timetable.html",
        {
            "timetable_entries": timetable_entries,
        },
    )


@login_required
def add_student(request, classroom_id):
    classroom = get_object_or_404(
        get_accessible_classrooms(request.user),
        id=classroom_id,
    )
    if not can_manage_classroom(request.user, classroom):
        messages.error(request, "You don't have permission to manage students.")
        return redirect("classroom_detail", classroom_id=classroom.id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        roll_no = request.POST.get("roll_no", "").strip()

        if not name or not roll_no.isdigit() or int(roll_no) < 1:
            messages.error(request, "Enter a valid name and roll number.")

        elif Student.objects.filter(classroom=classroom, roll_no=int(roll_no)).exists():
            messages.error(request, "This roll number already exists.")

        else:
            Student.objects.create(classroom=classroom, name=name, roll_no=int(roll_no))
            messages.success(request, "Student added successfully.")

    return redirect("classroom_detail", classroom_id=classroom.id)


@login_required
def edit_student(request, classroom_id, student_id):
    classroom = get_object_or_404(
        get_accessible_classrooms(request.user),
        id=classroom_id,
    )

    if not can_manage_classroom(request.user, classroom):
        messages.error(request, "You don't have permission to manage students.")
        return redirect("classroom_detail", classroom_id=classroom.id)
    student = get_object_or_404(Student, id=student_id, classroom=classroom)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        roll_no = request.POST.get("roll_no", "").strip()

        if not name or not roll_no.isdigit() or int(roll_no) < 1:
            messages.error(request, "Enter a valid name and roll number.")

        elif (
            Student.objects.filter(classroom=classroom, roll_no=int(roll_no))
            .exclude(id=student.id)
            .exists()
        ):
            messages.error(request, "This roll number already exists.")

        else:
            student.name = name
            student.roll_no = int(roll_no)
            student.save()

            messages.success(request, "Student updated successfully.")

    return redirect("classroom_detail", classroom_id=classroom.id)


@login_required
def delete_student(request, classroom_id, student_id):
    classroom = get_object_or_404(
        get_accessible_classrooms(request.user),
        id=classroom_id,
    )

    if not can_manage_classroom(request.user, classroom):
        messages.error(request, "You don't have permission to manage students.")
        return redirect("classroom_detail", classroom_id=classroom.id)
    student = get_object_or_404(Student, id=student_id, classroom=classroom)

    if request.method == "POST":
        student.delete()
        messages.success(request, "Student deleted successfully.")

    return redirect("classroom_detail", classroom_id=classroom.id)


@login_required
def mark_attendance(request, timetable_entry_id):
    timetable_entry = get_object_or_404(
        TimetableEntry.objects.select_related(
            "assignment__classroom",
            "assignment__subject",
            "assignment__teacher",
        ),
        id=timetable_entry_id,
    )

    assignment = timetable_entry.assignment
    classroom = assignment.classroom

    # Check teacher permissions
    if request.user.role == User.Role.TEACHER:
        if assignment.teacher_id != request.user.id:
            messages.error(request, "You cannot mark attendance for this subject.")
            return redirect("dashboard")

    elif request.user.role != User.Role.ADMIN:
        return redirect("dashboard")

    students = classroom.students.order_by("roll_no")

    if not students.exists():
        messages.error(
            request,
            "Add students to this classroom before marking attendance.",
        )
        return redirect("classroom_detail", classroom_id=classroom.id)

    selected_date = request.GET.get("date", date.today().isoformat())

    if request.method == "POST":
        selected_date = request.POST.get("class_date", "")

    try:
        selected_date = date.fromisoformat(selected_date)

        if selected_date.strftime("%a").upper() != timetable_entry.weekday:
            raise ValueError

    except (ValueError, TypeError):
        messages.error(request, "Please select a valid date for this class.")
        return redirect("mark_attendance", timetable_entry_id=timetable_entry.id)

    if request.method == "POST":
        attendance_data = []

        for student in students:
            status = request.POST.get(f"status_{student.id}")

            if status not in ["PRESENT", "ABSENT"]:
                messages.error(
                    request,
                    "Please mark every student as Present or Absent.",
                )

                return redirect(
                    f"{reverse('mark_attendance', args=[timetable_entry.id])}"
                    f"?date={selected_date.isoformat()}"
                )

            attendance_data.append((student, status))

        with transaction.atomic():
            session, created = AttendanceSession.objects.get_or_create(
                timetable_entry=timetable_entry,
                class_date=selected_date,
            )

            for student, status in attendance_data:
                attendance, created = Attendance.objects.get_or_create(
                    session=session,
                    student=student,
                    defaults={"status": status},
                )

                if not created:
                    attendance.status = status

                attendance.full_clean()
                attendance.save()

        messages.success(request, "Attendance submitted successfully.")

        return redirect(
            f"{reverse('mark_attendance', args=[timetable_entry.id])}"
            f"?date={selected_date.isoformat()}"
        )

    session = AttendanceSession.objects.filter(
        timetable_entry=timetable_entry,
        class_date=selected_date,
    ).first()

    existing_attendance = {}

    if session:
        existing_attendance = {
            record.student_id: record.status
            for record in session.attendance_records.all()
        }

    attendance_list = [
        {
            "student": student,
            "status": existing_attendance.get(student.id, ""),
        }
        for student in students
    ]

    return render(
        request,
        "attendance/mark_attendance.html",
        {
            "classroom": classroom,
            "timetable_entry": timetable_entry,
            "attendance_list": attendance_list,
            "selected_date": selected_date,
            "session": session,
        },
    )


@login_required
def daily_report(request, timetable_entry_id):
    timetable_entry = get_object_or_404(
        TimetableEntry.objects.select_related(
            "assignment__classroom",
            "assignment__subject",
            "assignment__teacher",
        ),
        id=timetable_entry_id,
    )

    assignment = timetable_entry.assignment
    classroom = assignment.classroom

    if request.user.role == User.Role.TEACHER:
        if assignment.teacher_id != request.user.id:
            messages.error(request, "You cannot view this report.")
            return redirect("dashboard")

    elif request.user.role != User.Role.ADMIN:
        return redirect("dashboard")

    selected_date = request.GET.get("date", date.today().isoformat())

    try:
        selected_date = date.fromisoformat(selected_date)

        if selected_date.strftime("%a").upper() != timetable_entry.weekday:
            raise ValueError

    except (ValueError, TypeError):
        messages.error(request, "Please select a valid date.")
        return redirect("daily_report", timetable_entry_id=timetable_entry.id)

    session = AttendanceSession.objects.filter(
        timetable_entry=timetable_entry,
        class_date=selected_date,
    ).first()

    if session:
        attendance_records = session.attendance_records.select_related(
            "student"
        ).order_by("student__roll_no")
    else:
        attendance_records = Attendance.objects.none()

    total = attendance_records.count()
    present = attendance_records.filter(status=Attendance.Status.PRESENT).count()
    absent = attendance_records.filter(status=Attendance.Status.ABSENT).count()
    unmarked = classroom.students.count() - total

    return render(
        request,
        "attendance/daily_report.html",
        {
            "classroom": classroom,
            "timetable_entry": timetable_entry,
            "selected_date": selected_date,
            "session": session,
            "attendance_records": attendance_records,
            "total": total,
            "present": present,
            "absent": absent,
            "unmarked": unmarked,
        },
    )


@login_required
def classroom_report(request, classroom_id):
    classroom = get_object_or_404(
        get_accessible_classrooms(request.user),
        id=classroom_id,
    )

    if not can_manage_classroom(request.user, classroom):
        messages.error(
            request,
            "You don't have permission to view this classroom report.",
        )
        return redirect("classroom_detail", classroom_id=classroom.id)

    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()

    sessions = AttendanceSession.objects.filter(
        timetable_entry__assignment__classroom=classroom,
    )

    try:
        if start_date:
            start_date = date.fromisoformat(start_date)
            sessions = sessions.filter(class_date__gte=start_date)

        if end_date:
            end_date = date.fromisoformat(end_date)
            sessions = sessions.filter(class_date__lte=end_date)

        if start_date and end_date and start_date > end_date:
            raise ValueError

    except (ValueError, TypeError):
        messages.error(request, "Please select a valid date range.")
        return redirect("classroom_report", classroom_id=classroom.id)

    sessions = sessions.annotate(record_count=Count("attendance_records")).filter(
        record_count__gt=0
    )

    attendance_records = Attendance.objects.filter(session__in=sessions)

    subject_records = (
        attendance_records.values("session__timetable_entry__assignment__subject__name")
        .annotate(
            total=Count("id"),
            present_count=Count(
                "id",
                filter=Q(status=Attendance.Status.PRESENT),
            ),
        )
        .order_by("session__timetable_entry__assignment__subject__name")
    )

    subject_reports = []

    for record in subject_records:
        percentage = (
            record["present_count"] / record["total"] * 100
            if record["total"] > 0
            else 0
        )

        subject_reports.append(
            {
                "name": record["session__timetable_entry__assignment__subject__name"],
                "total": record["total"],
                "present": record["present_count"],
                "absent": record["total"] - record["present_count"],
                "percentage": round(percentage, 2),
            }
        )

    present = attendance_records.filter(status=Attendance.Status.PRESENT).count()

    absent = attendance_records.filter(status=Attendance.Status.ABSENT).count()

    total_records = present + absent
    total_sessions = sessions.count()

    attendance_percentage = (present / total_records) * 100 if total_records > 0 else 0

    return render(
        request,
        "attendance/classroom_report.html",
        {
            "classroom": classroom,
            "start_date": start_date,
            "end_date": end_date,
            "total_sessions": total_sessions,
            "total_records": total_records,
            "present": present,
            "absent": absent,
            "attendance_percentage": round(attendance_percentage, 2),
            "subject_reports": subject_reports,
        },
    )


@login_required
def student_report(request, student_id):
    student = get_object_or_404(
        Student.objects.select_related("classroom"),
        id=student_id,
    )

    classroom = student.classroom

    if request.user.role == User.Role.ADMIN:
        records = Attendance.objects.filter(student=student)

    elif request.user.role == User.Role.TEACHER:
        if classroom.class_teacher_id == request.user.id:
            records = Attendance.objects.filter(student=student)

        elif classroom.subject_assignments.filter(teacher=request.user).exists():
            records = Attendance.objects.filter(
                student=student,
                session__timetable_entry__assignment__teacher=request.user,
            )

        else:
            messages.error(
                request,
                "You don't have permission to view this report.",
            )
            return redirect("dashboard")

    else:
        return redirect("dashboard")

    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()

    try:
        if start_date:
            start_date = date.fromisoformat(start_date)
            records = records.filter(session__class_date__gte=start_date)

        if end_date:
            end_date = date.fromisoformat(end_date)
            records = records.filter(session__class_date__lte=end_date)

        if start_date and end_date and start_date > end_date:
            raise ValueError

    except (ValueError, TypeError):
        messages.error(request, "Please select a valid date range.")
        return redirect("student_report", student_id=student.id)

    records = records.select_related(
        "session__timetable_entry__assignment__subject",
        "session__timetable_entry__assignment__teacher",
    ).order_by("-session__class_date")

    total = records.count()
    present = records.filter(status=Attendance.Status.PRESENT).count()
    absent = total - present

    percentage = (present / total * 100) if total else 0

    return render(
        request,
        "attendance/student_report.html",
        {
            "student": student,
            "records": records,
            "total": total,
            "present": present,
            "absent": absent,
            "percentage": round(percentage, 2),
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@login_required
def teacher_report(request, teacher_id):
    teacher = get_object_or_404(
        User,
        id=teacher_id,
        role=User.Role.TEACHER,
    )

    if request.user.role == User.Role.ADMIN:
        assignments = SubjectAssignment.objects.filter(teacher=teacher)

    elif request.user.role == User.Role.TEACHER:
        if request.user.id == teacher.id:
            assignments = SubjectAssignment.objects.filter(teacher=teacher)
        else:
            assignments = SubjectAssignment.objects.filter(
                teacher=teacher,
                classroom__class_teacher=request.user,
            )

            if not assignments.exists():
                messages.error(
                    request,
                    "You don't have permission to view this report.",
                )
                return redirect("dashboard")

    else:
        return redirect("dashboard")

    assignments = assignments.select_related(
        "classroom",
        "subject",
    )

    sessions = AttendanceSession.objects.filter(
        timetable_entry__assignment__in=assignments
    )

    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()

    try:
        if start_date:
            start_date = date.fromisoformat(start_date)
            sessions = sessions.filter(class_date__gte=start_date)

        if end_date:
            end_date = date.fromisoformat(end_date)
            sessions = sessions.filter(class_date__lte=end_date)

        if start_date and end_date and start_date > end_date:
            raise ValueError

    except (ValueError, TypeError):
        messages.error(request, "Please select a valid date range.")
        return redirect("teacher_report", teacher_id=teacher.id)

    attendance_records = Attendance.objects.filter(session__in=sessions)

    subject_records = (
        attendance_records.values(
            "session__timetable_entry__assignment__classroom__name",
            "session__timetable_entry__assignment__subject__name",
        )
        .annotate(
            total=Count("id"),
            present_count=Count(
                "id",
                filter=Q(status=Attendance.Status.PRESENT),
            ),
        )
        .order_by(
            "session__timetable_entry__assignment__classroom__name",
            "session__timetable_entry__assignment__subject__name",
        )
    )

    subject_reports = []

    for record in subject_records:
        subject_reports.append(
            {
                "classroom": record[
                    "session__timetable_entry__assignment__classroom__name"
                ],
                "subject": record[
                    "session__timetable_entry__assignment__subject__name"
                ],
                "total": record["total"],
                "present": record["present_count"],
                "absent": record["total"] - record["present_count"],
                "percentage": (
                    round(
                        record["present_count"] / record["total"] * 100,
                        2,
                    )
                    if record["total"]
                    else 0
                ),
            }
        )

    total_sessions = sessions.count()
    total = attendance_records.count()

    present = attendance_records.filter(status=Attendance.Status.PRESENT).count()

    absent = total - present
    percentage = (present / total * 100) if total else 0

    return render(
        request,
        "attendance/teacher_report.html",
        {
            "teacher": teacher,
            "assignments": assignments,
            "total_sessions": total_sessions,
            "total": total,
            "present": present,
            "absent": absent,
            "percentage": round(percentage, 2),
            "start_date": start_date,
            "end_date": end_date,
            "subject_reports": subject_reports,
        },
    )
