from django import forms


class FiltroLicitacionesForm(forms.Form):
    year = forms.ChoiceField(
        required=False,
        label='Año',
        choices=[('', 'Todos')],
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    region = forms.ChoiceField(
        required=False,
        label='Región',
        choices=[('', 'Todas')],
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    comuna = forms.ChoiceField(
        required=False,
        label='Comuna',
        choices=[('', 'Todas')],
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    estado = forms.ChoiceField(
        required=False,
        label='Estado',
        choices=[('', 'Todos')] + [
            ('publicada', 'Publicada'),
            ('cerrada', 'Cerrada'),
            ('desierta', 'Desierta'),
            ('adjudicada', 'Adjudicada'),
            ('revocada', 'Revocada'),
            ('suspendida', 'Suspendida'),
        ],
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    q = forms.CharField(
        required=False,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar licitación...'
        })
    )

    def __init__(self, *args, **kwargs):
        años = kwargs.pop('años', [])
        regiones = kwargs.pop('regiones', [])
        comunas = kwargs.pop('comunas', [])
        super().__init__(*args, **kwargs)

        if años:
            self.fields['year'].choices = [('', 'Todos')] + [
                (y, y) for y in años]
        if regiones:
            self.fields['region'].choices = [('', 'Todas')] + [
                (r, r) for r in regiones]
        if comunas:
            self.fields['comuna'].choices = [('', 'Todas')] + [
                (c, c) for c in comunas]
