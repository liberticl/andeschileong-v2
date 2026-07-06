from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import FormView, TemplateView
from django.http import JsonResponse

from ciudadespendientes.utils import get_client_ip, get_location_from_ip
from ciudadespendientes.models import Zone
from .models import Account, Organization, RegistrationRequest, AccountActivationToken
from .forms import RegistrationRequestForm
from .utils import send_email


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client_ip = get_client_ip(self.request)
        context.update(get_location_from_ip(client_ip))
        return context


class StaffMixin(LoginRequiredMixin):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('welcome')
        return super().dispatch(request, *args, **kwargs)


class RegistrationRequestCreateView(FormView):
    template_name = 'accounts/registration_request.html'
    form_class = RegistrationRequestForm
    success_url = '/accounts/solicitud-exitosa/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('welcome')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.cleaned_data
        organization = data.get('organization')

        if organization and organization != '__nueva__':
            org_obj = Organization.objects.get(id=int(organization))
            org_name = org_obj.name
            org_type = org_obj.type or ''
            org_rut = org_obj.rut or ''
            org_country = org_obj.country or 'Chile'
        else:
            org_name = data.get('new_org_name', '')
            org_type = data.get('new_org_type', '')
            org_rut = data.get('new_org_rut', '')
            org_country = data.get('new_org_country', 'Chile')

        request_obj = RegistrationRequest(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            cellphone=data.get('cellphone', ''),
            access_section=data['access_section'],
            organization_name=org_name,
            organization_type=org_type,
            organization_rut=org_rut,
            organization_country=org_country,
            zone=data.get('zone'),
        )
        request_obj.save()
        self._notify_admin(request_obj)
        return super().form_valid(form)

    def _notify_admin(self, request_obj):
        admin_emails = list(
            Account.objects.filter(is_staff=True, is_superuser=True)
            .values_list('email', flat=True)
        )
        if admin_emails:
            send_email(
                subject='Nueva solicitud de registro - Andes Chile ONG',
                template_name='email/new_registration_request.html',
                context={'request_obj': request_obj},
                recipients=admin_emails
            )


class RegistrationRequestSuccessView(TemplateView):
    template_name = 'accounts/registration_request_success.html'


class ActivateAccountView(FormView):
    template_name = 'accounts/activate_account.html'
    success_url = '/accounts/activacion-completa/'

    def dispatch(self, request, *args, **kwargs):
        token_str = kwargs.get('token')
        try:
            activation_token = AccountActivationToken.objects.get(token=token_str)
        except AccountActivationToken.DoesNotExist:
            messages.error(request, 'Token de activación inválido.')
            return redirect('login')
        if not activation_token.is_valid():
            messages.error(request, 'El token de activación ha expirado o ya fue usado.')
            return redirect('login')
        if request.user.is_authenticated:
            return redirect('welcome')
        self.activation_token = activation_token
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        from django import forms as django_forms
        class SetPasswordForm(django_forms.Form):
            password = django_forms.CharField(
                label='Contraseña',
                widget=django_forms.PasswordInput(attrs={'class': 'form-control'}),
                min_length=8)
            password_confirm = django_forms.CharField(
                label='Confirmar contraseña',
                widget=django_forms.PasswordInput(attrs={'class': 'form-control'}),
                min_length=8)
            def clean(self):
                cleaned_data = super().clean()
                if cleaned_data.get('password') != cleaned_data.get('password_confirm'):
                    raise django_forms.ValidationError('Las contraseñas no coinciden.')
                return cleaned_data
        return SetPasswordForm

    def form_valid(self, form):
        activation_token = self.activation_token
        user = activation_token.user
        user.set_password(form.cleaned_data['password'])
        user.save()
        activation_token.is_used = True
        activation_token.save()
        messages.success(self.request, '¡Cuenta activada! Ya puedes iniciar sesión.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activation_token'] = self.activation_token
        return context


class ActivationCompleteView(TemplateView):
    template_name = 'accounts/activation_complete.html'


class ZonesAPIView(View):
    def get(self, request):
        country = request.GET.get('country')
        qs = Zone.objects.all()
        if country:
            qs = qs.filter(country=country)
        qs = qs.order_by('country', 'name')
        data = [{'id': z.id, 'name': z.name, 'zone_type': z.zone_type,
                 'country': z.country, 'region': z.region or ''} for z in qs]
        return JsonResponse(data, safe=False)


class RegionsAPIView(View):
    def get(self, request):
        country = request.GET.get('country', 'Chile')
        regions = (Zone.objects.filter(country=country)
                   .exclude(region__isnull=True)
                   .exclude(region='')
                   .values_list('region', flat=True)
                   .distinct()
                   .order_by('region'))
        data = [{'name': r} for r in regions]
        return JsonResponse(data, safe=False)


class ComunasByRegionAPIView(View):
    def get(self, request):
        country = request.GET.get('country', 'Chile')
        region = request.GET.get('region', '')
        comunas = (Zone.objects.filter(country=country, region=region)
                   .order_by('name'))
        data = [{'id': z.id, 'name': z.name} for z in comunas]
        return JsonResponse(data, safe=False)


class OrganizationsAPIView(View):
    def get(self, request):
        orgs = Organization.objects.filter(is_active=True).order_by('name')
        data = [{'id': o.id, 'name': o.name, 'type': o.type or '',
                 'country': o.country or '', 'region': o.region or '',
                 'comuna': o.comuna or ''} for o in orgs]
        return JsonResponse(data, safe=False)
