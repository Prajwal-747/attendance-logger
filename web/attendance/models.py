from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]


class Classroom(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=12, unique=True)
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="classrooms",
        limit_choices_to={"role": User.Role.TEACHER},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


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

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="attendance_records"
    )
    class_date = models.DateField()
    hour_no = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=7, choices=Status.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("student", "class_date", "hour_no"),
                name="unique_student_attendance_per_hour",
            ),
            models.CheckConstraint(
                condition=models.Q(hour_no__gte=1) & models.Q(hour_no__lte=6),
                name="valid_attendance_hour",
            ),
        ]
        ordering = ["class_date", "hour_no"]

    def __str__(self):
        return f"{self.student} - {self.class_date} - {self.status}"
