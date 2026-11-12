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
    is_lab = models.BooleanField(default=False)

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

    def get_occupied_periods(self):
        """Return all periods occupied by this timetable entry."""
        periods = {self.period}

        if self.assignment.subject.is_lab:
            periods.add(self.period + 1)

        return periods

    def clean(self):
        super().clean()

        if not self.assignment_id:
            return

        is_lab = self.assignment.subject.is_lab

        if is_lab and self.period not in (1, 3, 5):
            raise ValidationError(
                {"period": "Labs can only start in periods 1, 3 or 5."}
            )

        current_periods = self.get_occupied_periods()

        conflicts = (
            TimetableEntry.objects.filter(weekday=self.weekday)
            .exclude(pk=self.pk)
            .select_related("assignment__subject")
        )

        for entry in conflicts:
            other_periods = entry.get_occupied_periods()

            if not current_periods.intersection(other_periods):
                continue

            if entry.assignment.classroom_id == self.assignment.classroom_id:
                raise ValidationError(
                    "This classroom already has a subject scheduled "
                    "during one of these periods."
                )

            if entry.assignment.teacher_id == self.assignment.teacher_id:
                raise ValidationError(
                    "This teacher is already assigned to another class "
                    "during one of these periods."
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


class AcademicCalendarDay(models.Model):
    class DayType(models.TextChoices):
        HOLIDAY = "HOLIDAY", "Holiday"
        WORKING = "WORKING", "Working Day"

    class TimetableWeekday(models.TextChoices):
        MONDAY = "MON", "Monday Timetable"
        TUESDAY = "TUE", "Tuesday Timetable"

    date = models.DateField(unique=True)
    day_type = models.CharField(
        max_length=10,
        choices=DayType.choices,
    )
    timetable_weekday = models.CharField(
        max_length=3,
        choices=TimetableWeekday.choices,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["date"]
        verbose_name = "Academic Calendar Day"
        verbose_name_plural = "Academic Calendar Days"

    def clean(self):
        super().clean()

        if self.day_type == self.DayType.WORKING and not self.timetable_weekday:
            raise ValidationError("Select which timetable to follow for a working day.")

        if self.day_type == self.DayType.HOLIDAY and self.timetable_weekday:
            raise ValidationError("A holiday cannot have a timetable assigned.")

    def __str__(self):
        if self.day_type == self.DayType.HOLIDAY:
            return f"{self.date} - Holiday"

        return f"{self.date} - {self.get_timetable_weekday_display()}"
