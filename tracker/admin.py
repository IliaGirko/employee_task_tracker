from django.contrib import admin

from tracker.models import Employee, Task


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "position")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "parent_task",
        "assigned_to",
        "due_date",
        "status",
        "priority",
        "created_at",
        "updated_at",
    )
