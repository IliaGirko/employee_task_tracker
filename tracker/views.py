from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from tracker.models import Employee, Task
from tracker.serializers import (
    EmployeeActiveTasksSerializer,
    EmployeeSerializer,
    TaskSerializer,
)


class EmployeeActiveTasksViewSet(viewsets.ReadOnlyModelViewSet):
    """Эндпоинт который возвращаем список сотрудников и их активные задачи отсортированные по кол-ву задач"""

    serializer_class = EmployeeActiveTasksSerializer

    def get_queryset(self):
        active_tasks = Task.objects.filter(status__in=["pending", "in_progress"])

        return (
            Employee.objects.annotate(
                num_active_tasks=Count(
                    "tasks", filter=Q(tasks__status__in=["pending", "in_progress"])
                )
            )
            .prefetch_related(Prefetch("tasks", queryset=active_tasks))
            .order_by("-num_active_tasks")
        )


class TaskViewSet(viewsets.ModelViewSet):
    """Вьювсет задач"""

    serializer_class = TaskSerializer
    queryset = Task.objects.all()


class EmployeeViewSet(viewsets.ModelViewSet):
    """Вьювсет сотрудников"""

    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()


class ImportantTasksView(APIView):
    """Эндпоинт для задач, не в работе, но от которых зависят задачи в работе + сотрудники, которые могут взять"""

    def get(self, request, *args, **kwargs):
        # Подзапрос на подзадачи в работе
        in_progress_subtasks = Task.objects.filter(
            parent_task=OuterRef("pk"), status="in_progress"
        )

        # Список важных задач
        important_tasks = (
            Task.objects.filter(status="pending")
            .annotate(has_in_progress_subtasks=Exists(in_progress_subtasks))
            .filter(has_in_progress_subtasks=True)
        )

        # Считаем количество активных задач на каждого сотрудника
        employees = Employee.objects.annotate(
            active_count=Count(
                "tasks", filter=Q(tasks__status__in=["pending", "in_progress"])
            )
        )
        # Словарь ID -> количество задач
        employee_task_counts = {emp.id: emp.active_count for emp in employees}
        # Получаем минимальное количество активных задач
        min_active_count = min(employee_task_counts.values() or [0])

        # Формируем ответ
        response_data = []

        for task in important_tasks:
            eligible_employees = []

            # Сотрудники с минимальной загрузкой
            eligible_employees.extend(employees.filter(active_count=min_active_count))

            # Сотрудник, выполняющий родительскую задачу
            if task.parent_task and task.parent_task.assigned_to:
                parent_employee = task.parent_task.assigned_to
                count = employee_task_counts.get(parent_employee.id, 0)
                if count <= min_active_count + 2:
                    eligible_employees.append(parent_employee)

            # Уникальные ФИО
            full_names = list({emp.full_name for emp in eligible_employees})

            response_data.append(
                {
                    "Важная задача": task.title,
                    "Срок": task.due_date,
                    "ФИО сотрудника": full_names,
                }
            )
        return Response(response_data)
