# -*- encoding: utf-8 -*-
from django import forms
from django.utils import timezone
from django.forms import widgets
from django.contrib.admin import widgets as widgets_admin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from ciudadespendientes.choices import COUNTRIES
from ciudadespendientes.models import Zone
from . import models
from .choices import ORGANIZATION_TYPES, ACCESS_SECTIONS, REQUEST_STATUS


class AccountCreationForm(forms.ModelForm):

    """
    A form for creating new users. Includes all the required fields.
    """
    # password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    # password2 = forms.CharField(
    #     label='Password confirmation', widget=forms.PasswordInput
    # )

    class Meta:
        model = models.Account
        fields = (
            'email', 'first_name', 'last_name', 'country',
            'birthdate', 'cellphone',
        )
        widgets = {
            'email': forms.TextInput(
                attrs={'required': 'required', 'class': 'input-block-level'}),
            'first_name': forms.TextInput(
                attrs={'class': 'input-block-level'}),
            'last_name': forms.TextInput(
                attrs={'class': 'input-block-level'}),
            'country': widgets.Select(
                attrs={'class': 'input-block-level'},
                choices=COUNTRIES),
            'birthdate': widgets_admin.AdminDateWidget(
                attrs={'class': 'input-block-level birthdate'}),
            'cellphone': forms.TextInput(
                attrs={'class': 'input-block-level'})}

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(AccountCreationForm, self).save(commit=False)
        # lowercase email just in case
        user.email = user.email.lower()

        # password = models.Account.objects.make_random_password()
        password = user.create_default_password()
        user.set_password(password)

        # last_login is a not null field
        user.last_login = timezone.now()

        if commit:
            user.save()

        # send mail to the user
        # user.send_email(password)

        return user


class AccountChangeForm(forms.ModelForm):

    """
    A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.

    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        fields = '__all__'
        model = models.Account

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class RegistrationRequestForm(forms.Form):
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@correo.com'}))
    first_name = forms.CharField(
        label='Nombre(s)', max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(
        label='Apellido(s)', max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    cellphone = forms.CharField(
        label='Celular (opcional)', max_length=56, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56912345678'}))
    access_section = forms.ChoiceField(
        label='¿Qué acceso necesitas?', choices=ACCESS_SECTIONS,
        widget=forms.Select(attrs={'class': 'form-control'}))
    zone = forms.ModelChoiceField(
        label='Zona', queryset=Zone.objects.all().order_by('country', 'name'),
        required=False, widget=forms.Select(attrs={'class': 'form-control'}))

    organization = forms.CharField(
        label='Organización', max_length=255,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Selecciona tu organización o elige "Otra" para crear una nueva.')
    new_org_name = forms.CharField(
        label='Nombre de la nueva organización', max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    new_org_type = forms.ChoiceField(
        label='Tipo de organización', choices=[('', '-- Selecciona --')] + list(ORGANIZATION_TYPES),
        required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    new_org_rut = forms.CharField(
        label='RUT (opcional)', max_length=40, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}))
    new_org_country = forms.ChoiceField(
        label='País', choices=[('', '-- Selecciona --')] + list(COUNTRIES),
        required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    new_org_region = forms.CharField(
        label='Región', max_length=255, required=False,
        widget=forms.Select(attrs={'class': 'form-control'}))
    new_org_comuna = forms.CharField(
        label='Comuna', max_length=255, required=False,
        widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import Organization
        org_choices = [('--nueva__', 'Otra (nueva organización)')]
        for org in Organization.objects.filter(is_active=True).order_by('name'):
            org_choices.append((str(org.id), org.name))
        self.fields['organization'].widget = forms.Select(
            attrs={'class': 'form-control'},
            choices=[('', '-- Selecciona tu organización --')] + org_choices)

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if models.Account.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        if models.RegistrationRequest.objects.filter(email=email, status='pending').exists():
            raise forms.ValidationError('Ya existe una solicitud pendiente para este correo.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        access_section = cleaned_data.get('access_section')
        zone = cleaned_data.get('zone')
        organization = cleaned_data.get('organization')

        if access_section == 'ciudadespendientes' and not zone:
            raise forms.ValidationError(
                'Debes seleccionar una zona para acceder a Ciudades Pendientes.')

        if organization == '__nueva__':
            new_name = cleaned_data.get('new_org_name', '').strip()
            new_type = cleaned_data.get('new_org_type', '').strip()
            new_country = cleaned_data.get('new_org_country', '').strip()
            new_region = cleaned_data.get('new_org_region', '').strip()
            new_comuna = cleaned_data.get('new_org_comuna', '').strip()
            if not new_name:
                self.add_error('new_org_name', 'El nombre de la organización es obligatorio.')
            if not new_type:
                self.add_error('new_org_type', 'El tipo de organización es obligatorio.')
            if not new_country:
                self.add_error('new_org_country', 'El país es obligatorio.')
            if not new_region:
                self.add_error('new_org_region', 'La región es obligatoria.')
            if not new_comuna:
                self.add_error('new_org_comuna', 'La comuna es obligatoria.')

        return cleaned_data


class RegistrationRequestRejectForm(forms.Form):
    reason = forms.CharField(
        label='Motivo del rechazo',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False)
