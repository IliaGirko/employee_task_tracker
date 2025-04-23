from django.db import models


class Employee(models.Model):
    """Модель сотрудников"""

    full_name = models.CharField("ФИО", max_length=100)
    position = models.CharField("Должность", max_length=100)

    def __str__(self):
        return self.full_name

    @property
    def active_tasks_count(self):
        return self.tasks.filter(status__in=["pending", "in_progress"]).count()

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"


class Task(models.Model):
    """Модель задач"""

    PRIORITY_CHOICES = (
        ("low", "Низкий"),
        ("medium", "Средний"),
        ("high", "Высокий"),
    )

    STATUS_CHOICES = (
        ("pending", "Ожидает"),
        ("in_progress", "В процессе"),
        ("done", "Завершена"),
        ("blocked", "Заблокирована"),
    )

    title = models.CharField("Наименование", max_length=200)

    parent_task = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subtasks",
        verbose_name="Родительская задача",
    )

    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Исполнитель",
        null=True,
        blank=True,
    )

    due_date = models.DateField("Срок")
    status = models.CharField(
        "Статус", max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    priority = models.CharField(
        "Приоритет", max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    def __str__(self):
        return self.title

    def is_active(self):
        return self.status in ["pending", "in_progress"]

    def is_important(self):
        """
        Важная задача:
        - Не в работе
        - От неё зависят задачи, которые уже в работе
        """
        if self.status != "pending":
            return False
        return self.subtasks.filter(status__in=["in_progress"]).exists()

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
