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
    AcademicCalendarDay,
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


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = (
        "assignment",
        "weekday",
        "period",
        "get_duration",
    )
    list_filter = ("weekday", "assignment__subject__is_lab")
    ordering = ("weekday", "period")

    @admin.display(description="Duration")
    def get_duration(self, obj):
        return "2 hours (Lab)" if obj.assignment.subject.is_lab else "1 hour"

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


admin.site.register(AttendanceSession)
admin.site.register(Student)
admin.site.register(Attendance)


@admin.register(AcademicCalendarDay)
class AcademicCalendarDayAdmin(admin.ModelAdmin):
    list_display = ("date", "day_type", "timetable_weekday")
    list_filter = ("day_type", "timetable_weekday")
    list_editable = ("day_type", "timetable_weekday")
    ordering = ("date",)
    date_hierarchy = "date"
