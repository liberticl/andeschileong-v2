from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django.utils.text import slugify
from django.utils import timezone
from .models import Activity, Noticia, Estudio
from .forms import ActivityForm, NoticiaForm, EstudioForm
from accounts.models import RegistrationRequest, AccountActivationToken, Account, Organization
from accounts.forms import RegistrationRequestRejectForm
from accounts.utils import send_email


def staff_required(u):
    return u.is_active and u.is_staff


@user_passes_test(staff_required, login_url='/login/')
def intranet_dashboard(request):
    from accounts.models import RegistrationRequest
    context = {
        'actividades_count': Activity.objects.filter(is_deleted=False).count(),
        'noticias_count': Noticia.objects.filter(is_deleted=False).count(),
        'estudios_count': Estudio.objects.filter(is_deleted=False).count(),
        'solicitudes_pendientes_count': RegistrationRequest.objects.filter(status='pending').count(),
    }
    return render(request, 'hugo_edit/intranet.html', context)


@user_passes_test(staff_required, login_url='/login/')
def restore_activity(request, pk):
    activity = Activity.objects.get(pk=pk)
    activity.restore()
    return redirect('hugo_activity_deleted')


@user_passes_test(staff_required, login_url='/login/')
def restore_noticia(request, pk):
    noticia = Noticia.objects.get(pk=pk)
    noticia.restore()
    return redirect('hugo_noticia_deleted')


@user_passes_test(staff_required, login_url='/login/')
def restore_estudio(request, pk):
    estudio = Estudio.objects.get(pk=pk)
    estudio.restore()
    return redirect('hugo_estudio_deleted')


class StaffMixin:
    @method_decorator(user_passes_test(staff_required, login_url='/login/'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class ActivityListView(StaffMixin, ListView):
    model = Activity
    template_name = 'hugo_edit/activity_list.html'
    context_object_name = 'activities'
    ordering = ['-date']
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset().filter(is_deleted=False)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['deleted_count'] = Activity.objects.filter(is_deleted=True).count()
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


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

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.POST.get('preview'):
            slug = slugify(self.object.title)
            return redirect(f'/actividades/{self.object.date.year}/{slug}/')
        return response


class ActivityDeleteView(StaffMixin, DeleteView):
    model = Activity
    template_name = 'hugo_edit/activity_confirm_delete.html'
    success_url = reverse_lazy('hugo_activity_list')

    def form_valid(self, form):
        self.object.soft_delete()
        return redirect(self.success_url)


class NoticiaListView(StaffMixin, ListView):
    model = Noticia
    template_name = 'hugo_edit/noticia_list.html'
    context_object_name = 'noticias'
    ordering = ['-date']
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset().filter(is_deleted=False)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['deleted_count'] = Noticia.objects.filter(is_deleted=True).count()
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


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

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.POST.get('preview'):
            slug = slugify(self.object.title)
            return redirect(f'/noticias/{self.object.date.year}/{slug}/')
        return response


class NoticiaDeleteView(StaffMixin, DeleteView):
    model = Noticia
    template_name = 'hugo_edit/noticia_confirm_delete.html'
    success_url = reverse_lazy('hugo_noticia_list')

    def form_valid(self, form):
        self.object.soft_delete()
        return redirect(self.success_url)


class EstudioListView(StaffMixin, ListView):
    model = Estudio
    template_name = 'hugo_edit/estudio_list.html'
    context_object_name = 'estudios'
    ordering = ['-date']
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset().filter(is_deleted=False)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['deleted_count'] = Estudio.objects.filter(is_deleted=True).count()
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


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

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.POST.get('preview'):
            slug = slugify(self.object.title)
            return redirect(f'/estudios/{self.object.date.year}/{slug}/')
        return response


class EstudioDeleteView(StaffMixin, DeleteView):
    model = Estudio
    template_name = 'hugo_edit/estudio_confirm_delete.html'
    success_url = reverse_lazy('hugo_estudio_list')

    def form_valid(self, form):
        self.object.soft_delete()
        return redirect(self.success_url)


class ActivityDeletedView(StaffMixin, ListView):
    model = Activity
    template_name = 'hugo_edit/activity_deleted.html'
    context_object_name = 'activities'
    ordering = ['-date']

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=True)


class NoticiaDeletedView(StaffMixin, ListView):
    model = Noticia
    template_name = 'hugo_edit/noticia_deleted.html'
    context_object_name = 'noticias'
    ordering = ['-date']

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=True)


class EstudioDeletedView(StaffMixin, ListView):
    model = Estudio
    template_name = 'hugo_edit/estudio_deleted.html'
    context_object_name = 'estudios'
    ordering = ['-date']

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=True)


class RegistrationRequestListView(StaffMixin, ListView):
    model = RegistrationRequest
    template_name = 'hugo_edit/registration_request_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_filter'] = self.request.GET.get('status', '')
        return context


class RegistrationRequestDetailView(StaffMixin, DetailView):
    model = RegistrationRequest
    template_name = 'hugo_edit/registration_request_detail.html'
    context_object_name = 'request_obj'


class RegistrationRequestApproveView(StaffMixin, View):
    def post(self, request, pk):
        registration_request = RegistrationRequest.objects.get(pk=pk)
        if registration_request.status != 'pending':
            messages.error(request, 'Esta solicitud ya fue procesada.')
            return redirect('hugo_registration_request_list')
        account, token = registration_request.approve(request.user)
        messages.success(
            request,
            f'Solicitud aprobada. Se envió email de activación a {account.email}.')
        return redirect('hugo_registration_request_list')


class RegistrationRequestRejectView(StaffMixin, FormView):
    form_class = RegistrationRequestRejectForm
    template_name = 'hugo_edit/registration_request_reject.html'
    success_url = reverse_lazy('hugo_registration_request_list')

    def form_valid(self, form):
        registration_request = RegistrationRequest.objects.get(pk=self.kwargs['pk'])
        if registration_request.status != 'pending':
            messages.error(self.request, 'Esta solicitud ya fue procesada.')
            return redirect('hugo_registration_request_list')
        reason = form.cleaned_data.get('reason', '')
        registration_request.reject(self.request.user, reason)
        messages.success(self.request, 'Solicitud rechazada.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_obj'] = RegistrationRequest.objects.get(pk=self.kwargs['pk'])
        return context
