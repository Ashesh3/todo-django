from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.forms import ModelForm, ValidationError
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from tasks.models import Task

from django.db import transaction


class AuthorisationCheck(LoginRequiredMixin):
    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)


class UserLoginView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True
    success_url = "/tasks"


class UserLogoutView(LoginRequiredMixin, LogoutView):
    redirect_authenticated_user = True
    success_url = "/user/logout"


class UserCreateView(CreateView):
    form_class = UserCreationForm
    template_name = "signup.html"
    success_url = "/user/login"


class TaskView(LoginRequiredMixin, ListView):
    template_name = "tasks.html"
    context_object_name = "tasks"

    def get_context_data(self, **kwargs):
        tasks = Task.objects.filter(deleted=False, user=self.request.user)
        context_data = super().get_context_data(**kwargs)
        context_data["completed_tasks"] = tasks.filter(completed=True).count()
        context_data["total_tasks"] = tasks.count()
        return context_data

    def get_queryset(self):
        tasks = Task.objects.filter(deleted=False, user=self.request.user)
        filter_term = self.request.GET.get("filter")
        if filter_term:
            tasks = tasks.filter(completed=(filter_term == "completed"))
        return tasks.order_by("priority")


def update_priorities(self, form):
    current_priority = form.instance.priority
    all_tasks = (
        Task.objects.filter(
            priority__gte=current_priority,
            deleted=False,
            completed=False,
            user=form.instance.user,
        )
        .exclude(pk=form.instance.id)
        .select_for_update()
        .order_by("priority")
    )

    with transaction.atomic():
        queries = []
        for task in all_tasks:
            if task.priority > current_priority:
                break
            current_priority = task.priority = task.priority + 1
            queries.append(task)
        if queries:
            Task.objects.bulk_update(queries, ["priority"], batch_size=100)
        self.object = form.save()


class TaskCreateForm(ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "priority", "completed"]


class TaskCreateView(LoginRequiredMixin, CreateView):
    form_class = TaskCreateForm
    template_name = "task_create.html"
    success_url = "/tasks"

    def form_valid(self, form):
        form.instance.user = self.request.user
        update_priorities(self, form)
        return super().form_valid(form)


class UpdateTaskView(AuthorisationCheck, UpdateView):
    model = Task
    form_class = TaskCreateForm
    template_name = "task_edit.html"
    success_url = "/tasks"

    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)

    def form_valid(self, form):
        update_priorities(self, form)
        return super().form_valid(form)


class DeleteTaskView(AuthorisationCheck, DeleteView):
    success_url = "/tasks"
    model = Task
    template_name = "task_delete.html"

    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)


def toggle_complete_task(request, pk):
    task = Task.objects.filter(id=pk, deleted=False, user=request.user)
    if task.exists():
        task.update(completed=not task[0].completed)
    return HttpResponseRedirect("/tasks")


def index_page(request):
    return HttpResponseRedirect("/tasks")
