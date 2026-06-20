from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """Redirige vers notre dashboard après connexion/inscription."""

    def get_login_redirect_url(self, request):
        return '/compte/tableau-de-bord/'


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Adapte la création de compte via Google/Apple à notre modèle User."""

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Utilise l'email comme username (requis par notre modèle)
        if not user.username:
            user.username = user.email
        # Les utilisateurs arrivant via social auth sont visiteurs par défaut
        if not user.role:
            user.role = 'visiteur'
        user.save()
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        return True
