from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Classroom, Student, Attendance
import secrets
import string
from django.contrib import messages
from datetime import date
from django.db import transaction
from django.urls import reverse


@login_required
def dashboard(request):
    classrooms = Classroom.objects.filter(teacher=request.user)

    return render(request, "attendance/dashboard.html", {"classrooms": classrooms})


def generate_class_code():
    characters = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(characters) for _ in range(8))


@login_required
def create_classroom(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if name:
            Classroom.objects.create(
                name=name, code=generate_class_code(), teacher=request.user
            )

        return redirect("dashboard")


@login_required
def classroom_detail(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)

    students = Student.objects.filter(classroom=classroom)

    return render(
        request,
        "attendance/classroom_detail.html",
        {"classroom": classroom, "students": students},
    )


@login_required
def add_student(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)

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
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)

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
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)

    student = get_object_or_404(Student, id=student_id, classroom=classroom)

    if request.method == "POST":
        student.delete()
        messages.success(request, "Student deleted successfully.")

    return redirect("classroom_detail", classroom_id=classroom.id)


@login_required
def mark_attendance(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)

    students = Student.objects.filter(classroom=classroom).order_by("roll_no")

    # Get the selected date and hour
    selected_date = request.GET.get("date", date.today().isoformat())
    selected_hour = request.GET.get("hour", "1")

    if request.method == "POST":
        selected_date = request.POST.get("class_date", "")
        selected_hour = request.POST.get("hour_no", "")

    # Validate date and hour
    try:
        selected_date = date.fromisoformat(selected_date)
        selected_hour = int(selected_hour)

        if not 1 <= selected_hour <= 6:
            raise ValueError

    except (ValueError, TypeError):
        messages.error(request, "Please select a valid date and hour.")
        return redirect("classroom_detail", classroom_id=classroom.id)

    # Handle attendance submission
    if request.method == "POST":
        attendance_data = []

        for student in students:
            status = request.POST.get(f"status_{student.id}")

            if status not in ["PRESENT", "ABSENT"]:
                messages.error(request, "Invalid attendance selection.")
                return redirect(
                    f"{reverse('mark_attendance', args=[classroom.id])}"
                    f"?date={selected_date.isoformat()}&hour={selected_hour}"
                )

            attendance_data.append((student, status))

        # Save all attendance records together
        with transaction.atomic():
            for student, status in attendance_data:
                Attendance.objects.update_or_create(
                    student=student,
                    class_date=selected_date,
                    hour_no=selected_hour,
                    defaults={"status": status},
                )

        messages.success(request, "Attendance submitted successfully.")

        return redirect(
            f"{reverse('mark_attendance', args=[classroom.id])}"
            f"?date={selected_date.isoformat()}&hour={selected_hour}"
        )

    # Fetch previously saved attendance
    existing_attendance = {
        record.student_id: record.status
        for record in Attendance.objects.filter(
            student__classroom=classroom,
            class_date=selected_date,
            hour_no=selected_hour,
        )
    }

    # Default new attendance selections to Present
    attendance_list = [
        {"student": student, "status": existing_attendance.get(student.id, "PRESENT")}
        for student in students
    ]

    return render(
        request,
        "attendance/mark_attendance.html",
        {
            "classroom": classroom,
            "attendance_list": attendance_list,
            "selected_date": selected_date,
            "selected_hour": selected_hour,
        },
    )


@login_required
def daily_report(request, classroom_id):
    classroom = get_object_or_404(
        Classroom,
        id=classroom_id,
        teacher=request.user,
    )

    selected_date = request.GET.get("date", date.today().isoformat())
    selected_hour = request.GET.get("hour", "1")

    try:
        selected_date = date.fromisoformat(selected_date)
        selected_hour = int(selected_hour)

        if not 1 <= selected_hour <= 6:
            raise ValueError

    except (ValueError, TypeError):
        messages.error(request, "Please select a valid date and hour.")
        return redirect("classroom_detail", classroom_id=classroom.id)

    attendance_records = (
        Attendance.objects.filter(
            student__classroom=classroom,
            class_date=selected_date,
            hour_no=selected_hour,
        )
        .select_related("student")
        .order_by("student__roll_no")
    )

    total = attendance_records.count()
    present = attendance_records.filter(status=Attendance.Status.PRESENT).count()
    absent = attendance_records.filter(status=Attendance.Status.ABSENT).count()
    unmarked = classroom.students.count() - total

    return render(
        request,
        "attendance/daily_report.html",
        {
            "classroom": classroom,
            "selected_date": selected_date,
            "selected_hour": selected_hour,
            "attendance_records": attendance_records,
            "total": total,
            "present": present,
            "absent": absent,
            "unmarked": unmarked,
        },
    )
