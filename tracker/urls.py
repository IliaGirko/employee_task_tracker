from django.urls import path
from rest_framework.routers import DefaultRouter

from tracker import views
from tracker.apps import TrackerConfig
from tracker.views import ImportantTasksView

app_name = TrackerConfig.name


router = DefaultRouter()

router.register(r"employees", views.EmployeeViewSet, basename="employees")
router.register(r"tasks", views.TaskViewSet, basename="tasks")
router.register(
    r"active_tasks", views.EmployeeActiveTasksViewSet, basename="active_tasks"
)

urlpatterns = [
    path("important_tasks/", ImportantTasksView.as_view(), name="important_tasks"),
] + router.urls
