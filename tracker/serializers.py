from datetime import date

from rest_framework import serializers

from tracker.models import Employee, Task


class EmployeeSerializer(serializers.ModelSerializer):
    """Сериализатор сотрудников"""

    class Meta:
        model = Employee
        fields = "__all__"

    def validate_full_name(self, value):
        if len(value.strip()) <= 5:
            raise serializers.ValidationError(
                "ФИО должно содержать не менее 5 символов."
            )
        return value


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор задач"""

    class Meta:
        model = Task
        fields = "__all__"

    def validate_due_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Срок задачи не может быть в прошлом.")
        return value


class EmployeeActiveTasksSerializer(serializers.ModelSerializer):
    """Сериализатор который возвращаем список сотрудников и их активные задачи"""

    tasks = TaskSerializer(many=True, read_only=True)
    num_active_tasks = serializers.IntegerField(read_only=True)

    class Meta:
        model = Employee
        fields = ["id", "full_name", "position", "num_active_tasks", "tasks"]
