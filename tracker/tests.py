from datetime import date, timedelta

from django.test import TestCase

from tracker.models import Employee, Task
from tracker.serializers import EmployeeSerializer, TaskSerializer


class EmployeeTests(TestCase):
    """Тестирование вьюшки сотрудников"""

    def test_valid_full_name(self):
        data = {"full_name": "Иванов Иван", "position": "Разработчик"}
        serializer = EmployeeSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_invalid_short_full_name(self):
        data = {"full_name": "Иван", "position": "Аналитик"}
        serializer = EmployeeSerializer(data=data)
        assert not serializer.is_valid()
        assert "full_name" in serializer.errors
        assert (
            serializer.errors["full_name"][0]
            == "ФИО должно содержать не менее 5 символов."
        )


class TaskTests(TestCase):
    """Тестирование вьюшки задач"""

    def test_due_date_valid(self):
        future_date = date.today() + timedelta(days=3)
        data = {
            "title": "Написать документацию",
            "status": "pending",
            "priority": "medium",
            "due_date": future_date,
        }
        serializer = TaskSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_due_date_in_past_invalid(self):
        past_date = date.today() - timedelta(days=1)
        data = {
            "title": "Просроченная задача",
            "status": "pending",
            "priority": "medium",
            "due_date": past_date,
        }
        serializer = TaskSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("due_date", serializer.errors)
        self.assertEqual(
            serializer.errors["due_date"][0], "Срок задачи не может быть в прошлом."
        )


class EmployeeActiveTasksTests(TestCase):
    """Тестирование активных задач"""

    def setUp(self):
        self.employee1 = Employee.objects.create(
            full_name="Иванов Иван", position="Разработчик"
        )
        self.employee2 = Employee.objects.create(
            full_name="Петров Петр", position="Тестировщик"
        )

        # Иванов — 2 активные задачи
        Task.objects.create(
            title="Задача 1",
            assigned_to=self.employee1,
            status="pending",
            priority="medium",
            due_date=date.today(),
        )
        Task.objects.create(
            title="Задача 2",
            assigned_to=self.employee1,
            status="in_progress",
            priority="high",
            due_date=date.today(),
        )

        # Петров — 1 активная, 1 завершённая
        Task.objects.create(
            title="Задача 3",
            assigned_to=self.employee2,
            status="pending",
            priority="low",
            due_date=date.today(),
        )
        Task.objects.create(
            title="Задача 4",
            assigned_to=self.employee2,
            status="done",
            priority="low",
            due_date=date.today(),
        )

    def test_active_tasks_viewset(self):
        response = self.client.get("/tracker/active_tasks/")
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # Проверка: Иванов должен быть первым (2 активные задачи)
        self.assertEqual(data[0]["id"], self.employee1.id)
        self.assertEqual(data[0]["num_active_tasks"], 2)

        # Проверка: Петров — второй (1 активная задача)
        self.assertEqual(data[1]["id"], self.employee2.id)
        self.assertEqual(data[1]["num_active_tasks"], 1)

        # Проверка: у каждого только активные задачи в списке
        for emp in data:
            for task in emp["tasks"]:
                self.assertIn(task["status"], ["pending", "in_progress"])


class ImportantTasksViewTests(TestCase):
    def setUp(self):
        # Сотрудники с разной нагрузкой
        self.emp_1 = Employee.objects.create(
            full_name="Иванов Иван", position="Инженер"
        )
        self.emp_2 = Employee.objects.create(full_name="Петров Петр", position="Техник")

        # Подзадача в работе, от нее зависит главная задача
        self.parent_task = Task.objects.create(
            title="Главная задача", status="pending", due_date=date.today()
        )

        self.subtask_in_progress = Task.objects.create(
            title="Подзадача в работе",
            status="in_progress",
            due_date=date.today(),
            parent_task=self.parent_task,
            assigned_to=self.emp_2,
        )

        # Дополнительные задачи для подсчета нагрузки
        Task.objects.create(
            title="Задача 1",
            status="pending",
            due_date=date.today(),
            assigned_to=self.emp_1,
        )  # нагрузка = 1
        Task.objects.create(
            title="Задача 2",
            status="in_progress",
            due_date=date.today(),
            assigned_to=self.emp_2,
        )  # нагрузка = 2

    def test_important_tasks_response(self):
        response = self.client.get("/tracker/important_tasks/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 1)

        task_data = data[0]

        # Проверка названия задачи и срока
        self.assertEqual(task_data["Важная задача"], "Главная задача")
        self.assertEqual(task_data["Срок"], str(date.today()))

        # Проверка, что Иванов Иван (наименее загружен) тоже есть
        self.assertIn("Иванов Иван", task_data["ФИО сотрудника"])
