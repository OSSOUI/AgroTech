from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


INPUT_CLASS = (
    'w-full px-4 py-3 rounded-lg border border-gray-300 '
    'focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent '
    'transition text-gray-700 placeholder-gray-400'
)


class InscriptionVendeurForm(UserCreationForm):
    first_name = forms.CharField(
        label='Prénom',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Votre prénom'})
    )
    last_name = forms.CharField(
        label='Nom',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Votre nom'})
    )
    email = forms.EmailField(
        label='Adresse e-mail',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'vous@exemple.com'})
    )
    telephone = forms.CharField(
        label='Téléphone',
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '+212 6XX XXX XXX'})
    )
    ville = forms.CharField(
        label='Ville',
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Votre ville'})
    )
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': '8 caractères minimum'})
    )
    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Répétez le mot de passe'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'telephone', 'ville', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.role = User.VENDEUR
        user.telephone = self.cleaned_data.get('telephone', '')
        user.ville = self.cleaned_data.get('ville', '')
        if commit:
            user.save()
        return user


class ConnexionForm(AuthenticationForm):
    username = forms.EmailField(
        label='Adresse e-mail',
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'vous@exemple.com',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Votre mot de passe'})
    )


class ProfilForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Prénom',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS})
    )
    last_name = forms.CharField(
        label='Nom',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS})
    )
    telephone = forms.CharField(
        label='Téléphone',
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS})
    )
    ville = forms.CharField(
        label='Ville',
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS})
    )
    bio = forms.CharField(
        label='Présentation',
        required=False,
        widget=forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3})
    )
    photo_profil = forms.ImageField(
        label='Photo de profil',
        required=False,
        widget=forms.FileInput(attrs={'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'telephone', 'ville', 'bio', 'photo_profil')
