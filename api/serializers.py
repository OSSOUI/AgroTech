from rest_framework import serializers
from accounts.models import User, Avis
from listings.models import Annonce, AnnoncePhoto, Favori
from messaging.models import Conversation, Message


class UserPublicSerializer(serializers.ModelSerializer):
    """Safe for public endpoints — no email, phone, or contact details."""
    note_moyenne = serializers.SerializerMethodField()
    nb_avis = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'photo_url', 'note_moyenne', 'nb_avis']

    def get_note_moyenne(self, obj):
        return obj.note_moyenne

    def get_nb_avis(self, obj):
        return obj.nb_avis

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo_profil and request:
            return request.build_absolute_uri(obj.photo_profil.url)
        return None


class UserMeSerializer(UserPublicSerializer):
    """Full data returned only to the authenticated user for /api/v1/moi/."""

    class Meta(UserPublicSerializer.Meta):
        fields = UserPublicSerializer.Meta.fields + [
            'email', 'telephone', 'whatsapp_number', 'ville', 'bio',
            'role', 'date_joined',
        ]


class InscriptionSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'telephone']

    def create(self, validated_data):
        email = validated_data['email']
        return User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            telephone=validated_data.get('telephone', ''),
        )


class AnnoncePhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = AnnoncePhoto
        fields = ['id', 'image_url', 'ordre']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class AnnonceListSerializer(serializers.ModelSerializer):
    vendeur = UserPublicSerializer(read_only=True)
    photo_principale = serializers.SerializerMethodField()
    prix_par_hectare = serializers.ReadOnlyField()
    region_display = serializers.CharField(source='get_region_display', read_only=True)
    type_culture_display = serializers.CharField(source='get_type_culture_display', read_only=True)
    type_titre_display = serializers.CharField(source='get_type_titre_foncier_display', read_only=True)
    class Meta:
        model = Annonce
        fields = [
            'id', 'titre', 'description', 'region', 'region_display',
            'ville', 'latitude', 'longitude', 'surface', 'prix',
            'prix_par_hectare', 'type_culture', 'type_culture_display',
            'type_titre_foncier', 'type_titre_display',
            'acces_eau', 'acces_route', 'electricite',
            'vues', 'statut', 'date_creation',
            'vendeur', 'photo_principale',
        ]

    def get_photo_principale(self, obj):
        request = self.context.get('request')
        photo = obj.photos.order_by('ordre').first()
        if photo and request:
            return request.build_absolute_uri(photo.image.url)
        return None


class AnnonceDetailSerializer(AnnonceListSerializer):
    photos = AnnoncePhotoSerializer(many=True, read_only=True)

    class Meta(AnnonceListSerializer.Meta):
        fields = AnnonceListSerializer.Meta.fields + ['photos']


class AvisSerializer(serializers.ModelSerializer):
    auteur = UserPublicSerializer(read_only=True)

    class Meta:
        model = Avis
        fields = ['id', 'auteur', 'note', 'commentaire', 'date_creation']
        read_only_fields = ['auteur', 'date_creation']

    def validate_note(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("La note doit être entre 1 et 5.")
        return value


class MessageSerializer(serializers.ModelSerializer):
    expediteur = UserPublicSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'expediteur', 'contenu', 'date_envoi', 'lu']


class ConversationSerializer(serializers.ModelSerializer):
    acheteur = UserPublicSerializer(read_only=True)
    vendeur = UserPublicSerializer(read_only=True)
    annonce = AnnonceListSerializer(read_only=True)
    dernier_message = serializers.SerializerMethodField()
    messages_non_lus = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'acheteur', 'vendeur', 'annonce',
                  'date_creation', 'dernier_message', 'messages_non_lus']

    def get_dernier_message(self, obj):
        # Use prefetched cache — avoid extra query per conversation
        msgs = sorted(obj.messages.all(), key=lambda m: m.date_envoi, reverse=True)
        if msgs:
            return {'contenu': msgs[0].contenu[:80], 'date': msgs[0].date_envoi}
        return None

    def get_messages_non_lus(self, obj):
        user = self.context['request'].user
        return sum(1 for m in obj.messages.all() if not m.lu and m.expediteur_id != user.id)
