from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Activity, Noticia, Estudio
from .forms import ActivityForm, NoticiaForm, EstudioForm

def staff_required(u):
    return u.is_active and u.is_staff

@user_passes_test(staff_required, login_url='/login/')
def intranet_dashboard(request):
    context = {
        'actividades_count': Activity.objects.count(),
        'noticias_count': Noticia.objects.count(),
        'estudios_count': Estudio.objects.count(),
    }
    return render(request, 'hugo_edit/intranet.html', context)

class StaffMixin:
    @method_decorator(user_passes_test(staff_required, login_url='/login/'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class ActivityListView(StaffMixin, ListView):
    model = Activity
    template_name = 'hugo_edit/activity_list.html'
    context_object_name = 'activities'
    ordering = ['-date']

class ActivityCreateView(StaffMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'hugo_edit/activity_form.html'
    success_url = reverse_lazy('hugo_activity_list')

class ActivityUpdateView(StaffMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'hugo_edit/activity_form.html'
    success_url = reverse_lazy('hugo_activity_list')

class ActivityDeleteView(StaffMixin, DeleteView):
    model = Activity
    template_name = 'hugo_edit/activity_confirm_delete.html'
    success_url = reverse_lazy('hugo_activity_list')


class NoticiaListView(StaffMixin, ListView):
    model = Noticia
    template_name = 'hugo_edit/noticia_list.html'
    context_object_name = 'noticias'
    ordering = ['-date']


class NoticiaCreateView(StaffMixin, CreateView):
    model = Noticia
    form_class = NoticiaForm
    template_name = 'hugo_edit/noticia_form.html'
    success_url = reverse_lazy('hugo_noticia_list')


class NoticiaUpdateView(StaffMixin, UpdateView):
    model = Noticia
    form_class = NoticiaForm
    template_name = 'hugo_edit/noticia_form.html'
    success_url = reverse_lazy('hugo_noticia_list')


class NoticiaDeleteView(StaffMixin, DeleteView):
    model = Noticia
    template_name = 'hugo_edit/noticia_confirm_delete.html'
    success_url = reverse_lazy('hugo_noticia_list')


class EstudioListView(StaffMixin, ListView):
    model = Estudio
    template_name = 'hugo_edit/estudio_list.html'
    context_object_name = 'estudios'
    ordering = ['-date']


class EstudioCreateView(StaffMixin, CreateView):
    model = Estudio
    form_class = EstudioForm
    template_name = 'hugo_edit/estudio_form.html'
    success_url = reverse_lazy('hugo_estudio_list')


class EstudioUpdateView(StaffMixin, UpdateView):
    model = Estudio
    form_class = EstudioForm
    template_name = 'hugo_edit/estudio_form.html'
    success_url = reverse_lazy('hugo_estudio_list')


class EstudioDeleteView(StaffMixin, DeleteView):
    model = Estudio
    template_name = 'hugo_edit/estudio_confirm_delete.html'
    success_url = reverse_lazy('hugo_estudio_list')
