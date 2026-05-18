# -*- encoding: utf-8 -*-
from django import forms
from django.utils import timezone
from django.forms import widgets
from django.contrib.admin import widgets as widgets_admin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from ciudadespendientes.choices import COUNTRIES
from . import models


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
