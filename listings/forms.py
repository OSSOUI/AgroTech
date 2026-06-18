from django import forms
from .models import Annonce, REGIONS, TYPES_CULTURE, TYPES_TITRE

INPUT_CLASS = (
    'w-full px-4 py-3 rounded-lg border border-gray-300 '
    'focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent '
    'transition text-gray-700'
)
SELECT_CLASS = INPUT_CLASS + ' bg-white'


class AnnonceForm(forms.ModelForm):
    titre = forms.CharField(
        label='Titre de l\'annonce',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: Terrain agricole fertile — Marrakech'})
    )
    description = forms.CharField(
        label='Description',
        widget=forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 5, 'placeholder': 'Décrivez le terrain, son environnement, ses atouts...'})
    )
    region = forms.ChoiceField(
        label='Région',
        choices=[('', 'Sélectionner une région...')] + list(REGIONS),
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    ville = forms.CharField(
        label='Ville / Commune',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: Marrakech'})
    )
    surface = forms.DecimalField(
        label='Surface (hectares)',
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': '0.00', 'step': '0.01'})
    )
    prix = forms.DecimalField(
        label='Prix demandé (MAD)',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': '0', 'step': '1000'})
    )
    type_culture = forms.ChoiceField(
        label='Type de culture adapté',
        choices=[('', 'Sélectionner un type...')] + list(TYPES_CULTURE),
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    type_titre_foncier = forms.ChoiceField(
        label='Titre foncier',
        choices=[('', 'Sélectionner...')] + list(TYPES_TITRE),
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    latitude = forms.DecimalField(
        label='Latitude (optionnel)',
        required=False,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: 31.6295', 'step': 'any'})
    )
    longitude = forms.DecimalField(
        label='Longitude (optionnel)',
        required=False,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: -7.9811', 'step': 'any'})
    )
    acces_eau = forms.BooleanField(label="Accès à l'eau", required=False)
    acces_route = forms.BooleanField(label='Accès route bitumée', required=False)
    electricite = forms.BooleanField(label='Électricité disponible', required=False)

    class Meta:
        model = Annonce
        fields = (
            'titre', 'description', 'region', 'ville',
            'surface', 'prix', 'type_culture', 'type_titre_foncier',
            'latitude', 'longitude',
            'acces_eau', 'acces_route', 'electricite',
        )


class FiltreAnnonceForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Rechercher un terrain...',
        })
    )
    region = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes les régions')] + list(REGIONS),
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    type_culture = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes les cultures')] + list(TYPES_CULTURE),
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    type_titre_foncier = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les titres')] + list(TYPES_TITRE),
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    prix_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Prix max (MAD)'})
    )
    surface_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Surface min (ha)', 'step': '0.1'})
    )
