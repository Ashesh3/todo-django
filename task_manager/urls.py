from django.contrib import admin
from django.urls import include, path
from tasks.views import (
    DeleteTaskView,
    UserLoginView,
    UserLogoutView,
    UserCreateView,
    TaskView,
    TaskCreateView,
    UpdateTaskView,
    toggle_complete_task,
    index_page,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),
    path("user/login/", UserLoginView.as_view()),
    path("user/logout/", UserLogoutView.as_view()),
    path("user/signup/", UserCreateView.as_view()),
    path("tasks/", TaskView.as_view()),
    path("add_task/", TaskCreateView.as_view()),
    path("update_task/<int:pk>", UpdateTaskView.as_view()),
    path("delete_task/<int:pk>", DeleteTaskView.as_view()),
    path("toggle_complete_task/<int:pk>", toggle_complete_task),
    path("", index_page),
]
