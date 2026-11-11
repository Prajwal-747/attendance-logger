from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email")}),
        ("Additional Information", {"fields": ("role",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "role", "password1", "password2"),
            },
        ),
    )


admin.site.register(Classroom)
admin.site.register(Subject)
admin.site.register(SubjectAssignment)
admin.site.register(TimetableEntry)
admin.site.register(AttendanceSession)
admin.site.register(Student)
admin.site.register(Attendance)
