from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "College Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]


class Classroom(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=12, unique=True)
    class_teacher = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="managed_classrooms",
        limit_choices_to={"role": User.Role.TEACHER},
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()

        if not self.pk or not self.class_teacher_id:
            return

        if not self.subject_assignments.filter(
            teacher_id=self.class_teacher_id
        ).exists():
            raise ValidationError(
                {
                    "class_teacher": (
                        "The class teacher must be assigned to at least one subject "
                        "in this classroom."
                    )
                }
            )

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SubjectAssignment(models.Model):
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="subject_assignments",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="classroom_assignments",
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="subject_assignments",
        limit_choices_to={"role": User.Role.TEACHER},
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("classroom", "subject"),
                name="unique_subject_per_classroom",
            )
        ]

    def __str__(self):
        return f"{self.classroom} - {self.subject} ({self.teacher})"


class TimetableEntry(models.Model):
    class Weekday(models.TextChoices):
        MONDAY = "MON", "Monday"
        TUESDAY = "TUE", "Tuesday"
        WEDNESDAY = "WED", "Wednesday"
        THURSDAY = "THU", "Thursday"
        FRIDAY = "FRI", "Friday"
        SATURDAY = "SAT", "Saturday"

    assignment = models.ForeignKey(
        SubjectAssignment,
        on_delete=models.CASCADE,
        related_name="timetable_entries",
    )
    weekday = models.CharField(max_length=3, choices=Weekday.choices)
    period = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("assignment", "weekday", "period"),
                name="unique_assignment_timetable_slot",
            ),
            models.CheckConstraint(
                condition=models.Q(period__gte=1) & models.Q(period__lte=6),
                name="valid_timetable_period",
            ),
        ]
        ordering = ["weekday", "period"]

    def clean(self):
        super().clean()

        if not self.assignment_id:
            return

        conflicts = TimetableEntry.objects.filter(
            weekday=self.weekday,
            period=self.period,
        ).exclude(pk=self.pk)

        # Check whether the classroom already has another subject.
        if conflicts.filter(assignment__classroom=self.assignment.classroom).exists():
            raise ValidationError(
                "This classroom already has a subject scheduled in this period."
            )

        # Check whether the teacher is already teaching elsewhere.
        if conflicts.filter(assignment__teacher=self.assignment.teacher).exists():
            raise ValidationError(
                "This teacher is already assigned to another class in this period."
            )

    def __str__(self):
        return (
            f"{self.assignment} - "
            f"{self.get_weekday_display()} - Period {self.period}"
        )


class AttendanceSession(models.Model):
    timetable_entry = models.ForeignKey(
        TimetableEntry,
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    class_date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("timetable_entry", "class_date"),
                name="unique_session_per_timetable_date",
            )
        ]
        ordering = ["-class_date"]

    def clean(self):
        super().clean()

        if not self.timetable_entry_id or not self.class_date:
            return

        expected_weekday = self.timetable_entry.weekday
        actual_weekday = self.class_date.strftime("%a").upper()

        if expected_weekday != actual_weekday:
            raise ValidationError(
                "The selected date does not match the scheduled weekday."
            )

    def __str__(self):
        return f"{self.timetable_entry.assignment.subject} - " f"{self.class_date}"


class Student(models.Model):
    class RegistrationStatus(models.TextChoices):
        UNREGISTERED = "UNREGISTERED", "Unregistered"
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"

    classroom = models.ForeignKey(
        Classroom, on_delete=models.CASCADE, related_name="students"
    )
    roll_no = models.PositiveIntegerField()
    name = models.CharField(max_length=150)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
    )
    registration_status = models.CharField(
        max_length=12,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.UNREGISTERED,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("classroom", "roll_no"), name="unique_roll_no_per_class"
            )
        ]

    def __str__(self):
        return f"{self.roll_no} - {self.name}"


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    status = models.CharField(max_length=7, choices=Status.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("session", "student"),
                name="unique_student_per_attendance_session",
            )
        ]

    def clean(self):
        super().clean()

        if not self.session_id or not self.student_id:
            return

        session_classroom_id = self.session.timetable_entry.assignment.classroom_id

        if self.student.classroom_id != session_classroom_id:
            raise ValidationError(
                "This student does not belong to the classroom for this session."
            )

    def __str__(self):
        return f"{self.student} - {self.session} - {self.status}"
