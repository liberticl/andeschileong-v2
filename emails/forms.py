from django import forms
from accounts.models import Account, Organization


class ComposeEmailForm(forms.Form):
    RECIPIENTS_CHOICES = [
        ('individual', 'Usuarios específicos'),
        ('all_active', 'Todos los usuarios activos'),
        ('organization', 'Usuarios de una organización'),
        ('custom_list', 'Lista de correos (no usuarios)'),
    ]

    recipients_type = forms.ChoiceField(
        choices=RECIPIENTS_CHOICES,
        label='Destinatarios',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'recipients-type',
        }))

    users = forms.ModelMultipleChoiceField(
        queryset=Account.objects.filter(is_active=True).order_by('email'),
        required=False,
        label='Seleccionar usuarios',
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '8',
        }))

    organization = forms.ModelChoiceField(
        queryset=Organization.objects.filter(is_active=True).order_by('name'),
        required=False,
        label='Organización',
        widget=forms.Select(attrs={
            'class': 'form-select',
        }))

    custom_emails = forms.CharField(
        required=False,
        label='Lista de correos',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Un correo por línea.\nOpcionalmente: correo@ejemplo.com, Nombre Apellido',
        }),
        help_text='Un correo por línea. Opcionalmente separar nombre con coma.')

    batch_label = forms.CharField(
        max_length=200,
        label='Nombre del lote',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Boletín julio 2026, Invitación evento...',
        }),
        help_text='Nombre descriptivo para identificar este envío en el historial.')

    subject = forms.CharField(
        max_length=500,
        label='Asunto',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))

    message = forms.CharField(
        label='Mensaje',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
        }),
        help_text='Cuerpo del correo. Se enviará como HTML.')

    def clean_custom_emails(self):
        data = self.cleaned_data.get('custom_emails', '')
        recipients_type = self.data.get('recipients_type')
        if recipients_type != 'custom_list':
            return data
        if not data.strip():
            raise forms.ValidationError(
                'Ingresa al menos un correo electrónico.')
        results = []
        for line in data.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if ',' in line:
                parts = line.split(',', 1)
                email = parts[0].strip()
                name = parts[1].strip()
            elif '\t' in line:
                parts = line.split('\t', 1)
                email = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else ''
            else:
                email = line
                name = ''
            if '@' not in email:
                raise forms.ValidationError(
                    f'Correo inválido: {email}')
            results.append({'email': email, 'name': name})
        if not results:
            raise forms.ValidationError(
                'Ingresa al menos un correo electrónico.')
        return results

    def clean(self):
        cleaned_data = super().clean()
        recipients_type = cleaned_data.get('recipients_type')

        if recipients_type == 'individual':
            if not cleaned_data.get('users'):
                raise forms.ValidationError(
                    'Selecciona al menos un usuario.')
        elif recipients_type == 'organization':
            if not cleaned_data.get('organization'):
                raise forms.ValidationError(
                    'Selecciona una organización.')
        elif recipients_type == 'custom_list':
            if not cleaned_data.get('custom_emails'):
                raise forms.ValidationError(
                    'Ingresa la lista de correos.')

        return cleaned_data

    def get_recipients(self):
        recipients_type = self.cleaned_data['recipients_type']
        results = []

        if recipients_type == 'individual':
            for user in self.cleaned_data['users']:
                results.append({
                    'email': user.email,
                    'name': user.get_fullname(),
                })

        elif recipients_type == 'all_active':
            for user in Account.objects.filter(is_active=True):
                results.append({
                    'email': user.email,
                    'name': user.get_fullname(),
                })

        elif recipients_type == 'organization':
            org = self.cleaned_data['organization']
            for user in org.users.filter(is_active=True):
                results.append({
                    'email': user.email,
                    'name': user.get_fullname(),
                })

        elif recipients_type == 'custom_list':
            results = self.cleaned_data['custom_emails']

        return results
