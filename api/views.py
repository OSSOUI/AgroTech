from django.db.models import Q, Exists, OuterRef, F
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User, Avis
from listings.models import Annonce, Favori, Boost, VueAnnonce
from messaging.models import Conversation, Message
from .serializers import (
    UserPublicSerializer, UserMeSerializer, InscriptionSerializer,
    AnnonceListSerializer, AnnonceDetailSerializer,
    AvisSerializer, ConversationSerializer, MessageSerializer,
)


# ── Auth ──────────────────────────────────────────────────────────

class InscriptionView(generics.CreateAPIView):
    serializer_class = InscriptionSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserMeSerializer(user, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class MoiView(generics.RetrieveUpdateAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ── Annonces ──────────────────────────────────────────────────────

class AnnonceListView(generics.ListAPIView):
    serializer_class = AnnonceListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        boost_qs = Boost.objects.filter(
            annonce=OuterRef('pk'), statut='actif', date_fin__gt=timezone.now()
        )
        qs = (
            Annonce.objects.filter(statut='active')
            .annotate(est_booste=Exists(boost_qs))
            .select_related('vendeur')
            .prefetch_related('photos')
            .order_by('-est_booste', '-date_creation')
        )

        q = self.request.query_params.get('q')
        region = self.request.query_params.get('region')
        type_culture = self.request.query_params.get('type_culture')
        prix_max = self.request.query_params.get('prix_max')
        surface_min = self.request.query_params.get('surface_min')

        if q:
            qs = qs.filter(Q(titre__icontains=q) | Q(ville__icontains=q) | Q(description__icontains=q))
        if region:
            qs = qs.filter(region=region)
        if type_culture:
            qs = qs.filter(type_culture=type_culture)
        if prix_max:
            qs = qs.filter(prix__lte=prix_max)
        if surface_min:
            qs = qs.filter(surface__gte=surface_min)

        return qs


class AnnonceDetailView(generics.RetrieveAPIView):
    serializer_class = AnnonceDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        boost_qs = Boost.objects.filter(
            annonce=OuterRef('pk'), statut='actif', date_fin__gt=timezone.now()
        )
        return (
            Annonce.objects.filter(statut='active')
            .annotate(est_booste=Exists(boost_qs))
            .select_related('vendeur')
            .prefetch_related('photos')
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Annonce.objects.filter(pk=instance.pk).update(vues=F('vues') + 1)
        if not request.user.is_authenticated or request.user != instance.vendeur:
            VueAnnonce.objects.create(annonce=instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# ── Favoris ───────────────────────────────────────────────────────

class FavorisView(generics.ListAPIView):
    serializer_class = AnnonceListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ids = Favori.objects.filter(utilisateur=self.request.user).values_list('annonce_id', flat=True)
        boost_qs = Boost.objects.filter(annonce=OuterRef('pk'), statut='actif', date_fin__gt=timezone.now())
        return (
            Annonce.objects.filter(pk__in=ids, statut='active')
            .annotate(est_booste=Exists(boost_qs))
            .select_related('vendeur')
            .prefetch_related('photos')
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_favori(request, pk):
    annonce = generics.get_object_or_404(Annonce, pk=pk, statut='active')
    favori, created = Favori.objects.get_or_create(utilisateur=request.user, annonce=annonce)
    if not created:
        favori.delete()
    return Response({'is_favori': created})


# ── Mes annonces ──────────────────────────────────────────────────

class MesAnnoncesView(generics.ListAPIView):
    serializer_class = AnnonceListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        boost_qs = Boost.objects.filter(annonce=OuterRef('pk'), statut='actif', date_fin__gt=timezone.now())
        return (
            Annonce.objects.filter(vendeur=self.request.user)
            .annotate(est_booste=Exists(boost_qs))
            .select_related('vendeur')
            .prefetch_related('photos')
            .order_by('-date_creation')
        )


# ── Profil vendeur ────────────────────────────────────────────────

class ProfilVendeurView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        vendeur = generics.get_object_or_404(User, pk=pk)
        boost_qs = Boost.objects.filter(annonce=OuterRef('pk'), statut='actif', date_fin__gt=timezone.now())
        annonces = (
            Annonce.objects.filter(vendeur=vendeur, statut='active')
            .annotate(est_booste=Exists(boost_qs))
            .prefetch_related('photos')
            .order_by('-est_booste', '-date_creation')[:6]
        )
        avis = Avis.objects.filter(vendeur=vendeur).select_related('auteur')

        peut_laisser_avis = False
        mon_avis = None
        if request.user.is_authenticated and request.user != vendeur:
            peut_laisser_avis = Conversation.objects.filter(
                acheteur=request.user, vendeur=vendeur
            ).exists()
            try:
                mon_avis = AvisSerializer(
                    Avis.objects.get(auteur=request.user, vendeur=vendeur),
                    context={'request': request}
                ).data
            except Avis.DoesNotExist:
                pass

        return Response({
            'vendeur': UserPublicSerializer(vendeur, context={'request': request}).data,
            'annonces': AnnonceListSerializer(annonces, many=True, context={'request': request}).data,
            'avis': AvisSerializer(avis, many=True, context={'request': request}).data,
            'peut_laisser_avis': peut_laisser_avis,
            'mon_avis': mon_avis,
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def laisser_avis(request, vendeur_pk):
    vendeur = generics.get_object_or_404(User, pk=vendeur_pk)
    if request.user == vendeur:
        return Response({'detail': 'Vous ne pouvez pas vous noter vous-même.'}, status=400)
    if not Conversation.objects.filter(acheteur=request.user, vendeur=vendeur).exists():
        return Response({'detail': 'Vous devez avoir contacté ce vendeur.'}, status=403)

    serializer = AvisSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    avis, _ = Avis.objects.update_or_create(
        auteur=request.user, vendeur=vendeur,
        defaults={
            'note': serializer.validated_data['note'],
            'commentaire': serializer.validated_data.get('commentaire', ''),
        }
    )
    return Response(AvisSerializer(avis, context={'request': request}).data)


# ── Messagerie ────────────────────────────────────────────────────

class ConversationsView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Conversation.objects.filter(Q(acheteur=user) | Q(vendeur=user))
            .select_related('acheteur', 'vendeur', 'annonce')
            .prefetch_related('messages')
            .order_by('-date_creation')
        )


class MessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conv_id = self.kwargs['conv_id']
        user = self.request.user
        conv = generics.get_object_or_404(
            Conversation,
            pk=conv_id,
        )
        if conv.acheteur != user and conv.vendeur != user:
            return Message.objects.none()
        # Marquer comme lus
        conv.messages.filter(lu=False).exclude(expediteur=user).update(lu=True)
        return conv.messages.select_related('expediteur').order_by('date_envoi')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def envoyer_message(request, annonce_pk):
    annonce = generics.get_object_or_404(Annonce, pk=annonce_pk, statut='active')
    if request.user == annonce.vendeur:
        return Response({'detail': 'Vous ne pouvez pas vous envoyer un message.'}, status=400)

    contenu = request.data.get('contenu', '').strip()
    if not contenu:
        return Response({'detail': 'Le message ne peut pas être vide.'}, status=400)

    conv, _ = Conversation.objects.get_or_create(
        acheteur=request.user,
        vendeur=annonce.vendeur,
        annonce=annonce,
    )
    msg = Message.objects.create(conversation=conv, expediteur=request.user, contenu=contenu)
    return Response(MessageSerializer(msg, context={'request': request}).data, status=201)
