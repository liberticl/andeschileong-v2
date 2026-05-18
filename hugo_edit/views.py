from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Activity
from .forms import ActivityForm

def superuser_required(u):
    return u.is_active and u.is_superuser

@user_passes_test(superuser_required, login_url='/login/')
def intranet_dashboard(request):
    return render(request, 'hugo_edit/intranet.html')

class SuperuserMixin:
    @method_decorator(user_passes_test(superuser_required, login_url='/login/'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class ActivityListView(SuperuserMixin, ListView):
    model = Activity
    template_name = 'hugo_edit/activity_list.html'
    context_object_name = 'activities'
    ordering = ['-date']

class ActivityCreateView(SuperuserMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'hugo_edit/activity_form.html'
    success_url = reverse_lazy('hugo_activity_list')

class ActivityUpdateView(SuperuserMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'hugo_edit/activity_form.html'
    success_url = reverse_lazy('hugo_activity_list')

class ActivityDeleteView(SuperuserMixin, DeleteView):
    model = Activity
    template_name = 'hugo_edit/activity_confirm_delete.html'
    success_url = reverse_lazy('hugo_activity_list')
