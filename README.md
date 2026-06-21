# AgroTech — Marketplace de Terrains Agricoles au Maroc

Plateforme de mise en relation entre vendeurs et acheteurs de terrains agricoles marocains. Permet de publier, rechercher, comparer et contacter via des annonces géolocalisées.

---

## Table des matières

1. [Stack technique](#stack-technique)
2. [Architecture du projet](#architecture-du-projet)
3. [Installation et lancement](#installation-et-lancement)
4. [Modèles de données](#modèles-de-données)
5. [Fonctionnalités Web](#fonctionnalités-web)
6. [URLs Web](#urls-web)
7. [API REST (Mobile)](#api-rest-mobile)
8. [Application Mobile Flutter](#application-mobile-flutter)
9. [Variables d'environnement](#variables-denvironnement)
10. [Commandes utiles](#commandes-utiles)

---

## Stack technique

### Backend
| Technologie | Version | Rôle |
|---|---|---|
| Python | 3.x | Langage principal |
| Django | 6.0.6 | Framework web |
| PostgreSQL | — | Base de données |
| Django REST Framework | 3.16.0 | API REST pour le mobile |
| djangorestframework-simplejwt | 5.5.0 | Authentification JWT |
| django-allauth | 65.18.0 | Auth sociale + reset mot de passe |
| django-cors-headers | 4.7.0 | CORS pour Flutter/mobile |
| Pillow | 12.2.0 | Traitement des images |
| python-decouple | 3.8 | Variables d'environnement |
| psycopg2-binary | 2.9.12 | Connecteur PostgreSQL |

### Frontend Web
| Technologie | Rôle |
|---|---|
| Django Templates | Rendu HTML côté serveur |
| Tailwind CSS (CDN) | Framework CSS utilitaire |
| JavaScript vanilla | Interactions (simulateur, filtres) |
| Leaflet.js 1.9.4 | Cartes interactives (OpenStreetMap) |

### Application Mobile
| Technologie | Version | Rôle |
|---|---|---|
| Flutter | 3.32.4 | Framework mobile cross-platform |
| Dart | 3.8.1 | Langage Flutter |
| Android Studio | — | Environnement de développement Android |

---

## Architecture du projet

```
agroTech/
├── config/                  # Configuration Django
│   ├── settings.py          # Paramètres (DB, auth, DRF, CORS…)
│   ├── urls.py              # Routeur principal
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                # Module utilisateurs
│   ├── models.py            # User (custom), Avis
│   ├── views.py             # Inscription, connexion, dashboard, profil vendeur
│   ├── urls.py
│   ├── forms.py
│   └── adapter.py           # Adapteur django-allauth
│
├── listings/                # Module annonces
│   ├── models.py            # Annonce, AnnoncePhoto, Boost, VueAnnonce, Favori
│   ├── views.py             # Liste, détail, CRUD, favoris, boost, comparaison
│   └── urls.py
│
├── messaging/               # Module messagerie
│   ├── models.py            # Conversation, Message
│   ├── views.py             # Inbox, conversation, démarrer
│   └── urls.py
│
├── api/                     # API REST (pour Flutter)
│   ├── serializers.py       # Sérialisation JSON de tous les modèles
│   ├── views.py             # Vues API (auth, annonces, favoris, messages…)
│   └── urls.py              # Routes /api/v1/
│
├── templates/               # Templates HTML
│   ├── base.html            # Layout principal (navbar, footer)
│   ├── home.html            # Page d'accueil
│   ├── accounts/            # Connexion, inscription, dashboard, profil
│   ├── listings/            # Liste, détail, créer, modifier, favoris, boost
│   ├── messaging/           # Inbox, conversation
│   └── partials/            # Composants réutilisables (carte annonce)
│
├── media/                   # Fichiers uploadés (images)
├── requirements.txt
└── manage.py
```

---

## Structure détaillée — rôle de chaque fichier

### `config/`
| Fichier | Rôle |
|---|---|
| `settings.py` | Paramètres globaux : base de données, apps installées, auth, DRF, JWT, CORS, Tailwind, media |
| `urls.py` | Routeur principal — connecte `/`, `/compte/`, `/terrains/`, `/messages/`, `/api/v1/`, `/auth/` |
| `wsgi.py` / `asgi.py` | Points d'entrée serveur (production) |

---

### `accounts/`
| Fichier | Rôle |
|---|---|
| `models.py` | `User` (custom AbstractUser, login par email) + `Avis` (note 1-5 d'un acheteur sur un vendeur) |
| `views.py` | `inscription`, `connexion`, `deconnexion`, `tableau_de_bord` (stats vendeur), `profil` (édition), `profil_vendeur` (page publique), `analytics_vendeur` (graphiques 14j), `laisser_avis` |
| `forms.py` | `InscriptionVendeurForm`, `ConnexionForm`, `ProfilForm` |
| `urls.py` | Routes `/compte/*` |
| `adapter.py` | Adapteur django-allauth : force l'email comme identifiant, désactive la vérification email en dev |
| `admin.py` | Enregistrement du modèle User dans l'admin Django |

---

### `listings/`
| Fichier | Rôle |
|---|---|
| `models.py` | `Annonce` (terrain + GPS + caractéristiques), `AnnoncePhoto` (galerie), `Boost` (mise en avant payante), `VueAnnonce` (historique quotidien des vues), `Favori` (utilisateur ↔ annonce) |
| `views.py` | `home` (page d'accueil avec stats), `liste_annonces` (filtres + carte + pagination), `detail_annonce` (carte Leaflet + simulateur + vues), `creer_annonce`, `modifier_annonce`, `supprimer_annonce`, `toggle_favori`, `mes_favoris`, `comparer_annonces`, `commander_boost`, `boost_confirmation` |
| `forms.py` | `AnnonceForm` (création/édition avec lat/lng), `FiltreAnnonceForm` (filtres de recherche) |
| `urls.py` | Routes `/terrains/*` |
| `admin.py` | Interface admin pour Annonce, Photo, Boost, VueAnnonce |

**Constantes importantes dans `views.py` :**
- `COORDS_REGIONS` — coordonnées GPS du centre de chaque région (fallback carte quand pas de GPS)
- `BOOST_PACKAGES` — tarifs et labels des formules de boost (7j/199 MAD, 14j/349 MAD, 30j/599 MAD)

---

### `messaging/`
| Fichier | Rôle |
|---|---|
| `models.py` | `Conversation` (unique par annonce+acheteur), `Message` (contenu + statut lu/non lu) |
| `views.py` | `inbox` (boîte de réception avec compteur non lus), `conversation` (fil de messages), `demarrer_conversation` (initier le contact depuis une annonce) |
| `urls.py` | Routes `/messages/*` |
| `context_processors.py` | Injecte `nb_messages_non_lus` dans tous les templates (badge dans la navbar) |

---

### `api/`
| Fichier | Rôle |
|---|---|
| `serializers.py` | Conversion modèles → JSON : `UserPublicSerializer`, `InscriptionSerializer`, `AnnonceListSerializer`, `AnnonceDetailSerializer`, `AvisSerializer`, `MessageSerializer`, `ConversationSerializer` |
| `views.py` | Vues DRF : `InscriptionView`, `MoiView`, `AnnonceListView`, `AnnonceDetailView`, `FavorisView`, `toggle_favori`, `MesAnnoncesView`, `ProfilVendeurView`, `laisser_avis`, `ConversationsView`, `MessagesView`, `envoyer_message` |
| `urls.py` | Routes `/api/v1/*` |
| `apps.py` | Déclaration de l'app Django `api` |

---

### `templates/`
| Fichier | Rôle |
|---|---|
| `base.html` | Layout commun : navbar, footer, Tailwind CDN, fix CSS Leaflet, messages Django |
| `home.html` | Page d'accueil : annonces récentes + stats générales |
| `partials/annonce_card.html` | Composant carte d'annonce réutilisé dans liste, favoris, dashboard |
| `accounts/inscription.html` | Formulaire d'inscription |
| `accounts/connexion.html` | Formulaire de connexion |
| `accounts/tableau_de_bord.html` | Dashboard vendeur : mes annonces, statuts, lien analytiques |
| `accounts/profil.html` | Formulaire modification du profil (photo, bio, téléphone…) |
| `accounts/profil_vendeur.html` | Page publique d'un vendeur : annonces, note, avis, bouton contacter |
| `accounts/analytics.html` | Graphique vues 14j (Chart.js), tableau stats par annonce |
| `listings/liste.html` | Liste des annonces avec filtres, pagination et carte Leaflet globale |
| `listings/detail.html` | Détail terrain : galerie, infos, carte Leaflet, simulateur de financement, messagerie |
| `listings/creer.html` | Formulaire création annonce avec picker GPS Leaflet |
| `listings/modifier.html` | Formulaire édition annonce avec picker GPS pré-rempli |
| `listings/supprimer.html` | Confirmation de suppression |
| `listings/mes_favoris.html` | Grille des annonces mises en favori |
| `listings/comparer.html` | Tableau comparatif (jusqu'à 3 annonces, colonnes équilibrées) |
| `listings/boost_commander.html` | Choix de la formule de boost (Starter/Pro/Premium) |
| `listings/boost_confirmation.html` | Confirmation de commande boost |
| `messaging/inbox.html` | Boîte de réception : liste des conversations avec aperçu du dernier message |
| `messaging/conversation.html` | Fil de discussion avec formulaire d'envoi |
| `account/password_reset*.html` | Templates de reset mot de passe (django-allauth) |

---

## Installation et lancement

### Prérequis
- Python 3.10+
- PostgreSQL
- pip

### 1. Cloner et créer l'environnement virtuel

```bash
git clone https://github.com/OSSOUI/AgroTech.git
cd AgroTech
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurer les variables d'environnement

Créer un fichier `.env` à la racine :

```env
SECRET_KEY=votre_clé_secrète_django
DEBUG=True
DB_NAME=agrotech
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432
```

### 3. Base de données et migrations

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Lancer le serveur

```bash
python manage.py runserver
```

L'application est disponible sur `http://localhost:8000`

---

## Modèles de données

### User (accounts)
Modèle personnalisé étendant `AbstractUser`. L'email est le champ d'authentification principal.

| Champ | Type | Description |
|---|---|---|
| email | EmailField (unique) | Identifiant de connexion |
| role | CharField | `vendeur` ou `visiteur` |
| telephone | CharField | Numéro formaté automatiquement pour WhatsApp |
| ville | CharField | Ville de résidence |
| bio | TextField | Description du profil |
| photo_profil | ImageField | Avatar |

**Propriétés calculées :** `note_moyenne`, `nb_avis`, `whatsapp_number`, `is_vendeur`

---

### Annonce (listings)
Terrain agricole mis en vente ou en location.

| Champ | Type | Description |
|---|---|---|
| vendeur | FK → User | Propriétaire de l'annonce |
| titre | CharField | Titre de l'annonce |
| description | TextField | Description détaillée |
| region | CharField | 1 des 12 régions du Maroc |
| ville | CharField | Ville du terrain |
| latitude / longitude | DecimalField | Coordonnées GPS (optionnelles) |
| surface | DecimalField | Surface en hectares |
| prix | DecimalField | Prix en MAD |
| type_culture | CharField | Céréales, maraîchage, olivier… |
| type_titre_foncier | CharField | Melkia, collectif, domanial… |
| acces_eau | BooleanField | Accès à l'eau |
| acces_route | BooleanField | Accès route |
| electricite | BooleanField | Électricité disponible |
| statut | CharField | `active`, `en_attente`, `desactivee` |
| vues | PositiveIntegerField | Compteur de vues |

**Propriétés calculées :** `prix_par_hectare`, `is_boosted`, `boost_actif`

**Régions disponibles :** Tanger-Tétouan, Oriental, Fès-Meknès, Rabat-Salé, Béni Mellal, Casablanca, Marrakech, Drâa-Tafilalet, Souss-Massa, Guelmim, Laâyoune, Dakhla

---

### AnnoncePhoto (listings)
Photos associées à une annonce, ordonnées par `ordre`.

---

### Boost (listings)
Mise en avant payante d'une annonce.

| Durée | Tarif |
|---|---|
| 7 jours | 199 MAD |
| 14 jours | 349 MAD |
| 30 jours | 599 MAD |

Statuts : `en_attente`, `actif`, `expire`, `annule`

---

### Favori (listings)
Association unique utilisateur ↔ annonce.

---

### VueAnnonce (listings)
Historique quotidien des vues par annonce (pour les analytiques vendeur).

---

### Avis (accounts)
Note (1-5) laissée par un acheteur sur un vendeur, conditionnée par l'existence d'une conversation.

---

### Conversation / Message (messaging)
Une conversation est unique par triplet (annonce, acheteur, vendeur). Les messages sont triés chronologiquement avec statut `lu/non lu`.

---

## Fonctionnalités Web

### Gestion des annonces
- Lister et filtrer les annonces (région, type culture, prix max, surface min, recherche texte)
- Voir le détail avec galerie photos, carte Leaflet, simulateur de financement
- Créer / modifier / supprimer une annonce (vendeurs uniquement)
- Picker de localisation GPS interactif sur le formulaire
- Comparer jusqu'à 3 annonces côte à côte

### Carte interactive (Leaflet.js)
- Carte globale sur la page liste : affiche toutes les annonces (marqueur vert = GPS précis, marron = centre de région approximatif)
- Carte détail : zoom sur le terrain ou sur la région si pas de GPS
- Carte picker sur les formulaires créer/modifier : clic pour placer l'épingle, glisser pour ajuster

### Compte utilisateur
- Inscription / connexion par email
- Réinitialisation du mot de passe (django-allauth)
- Tableau de bord vendeur avec statistiques
- Analytiques : graphiques de vues sur 30 jours par annonce
- Profil public vendeur avec ses annonces et ses avis

### Messagerie
- Boîte de réception avec compteur de messages non lus
- Conversation par annonce (un acheteur = une conversation par annonce)
- Messages en temps réel (rechargement de page)

### Favoris
- Ajouter / retirer des favoris (toggle)
- Page "Mes favoris"

### Boost (mise en avant)
- Commander un boost depuis la page d'annonce
- Les annonces boostées apparaissent en premier dans la liste

### Simulateur de financement
- Présent sur chaque page de détail
- Calcule la mensualité (formule prêt amortissable)
- Paramètres : apport, durée (10/15/20 ans), taux (3-7%)
- Affichage en MAD (format fr-MA)

---

## URLs Web

### Annonces — `/terrains/`
| URL | Vue | Description |
|---|---|---|
| `/terrains/` | `liste_annonces` | Liste + filtres + carte globale |
| `/terrains/<id>/` | `detail_annonce` | Détail, galerie, simulateur, carte |
| `/terrains/deposer/` | `creer_annonce` | Formulaire de création |
| `/terrains/<id>/modifier/` | `modifier_annonce` | Formulaire d'édition |
| `/terrains/<id>/supprimer/` | `supprimer_annonce` | Suppression |
| `/terrains/<id>/favori/` | `toggle_favori` | Ajouter/retirer favori (POST) |
| `/terrains/mes-favoris/` | `mes_favoris` | Liste des favoris |
| `/terrains/comparer/` | `comparer_annonces` | Tableau comparatif |
| `/terrains/<id>/boost/` | `commander_boost` | Commander un boost |
| `/terrains/boost/<id>/confirmation/` | `boost_confirmation` | Confirmation boost |

### Compte — `/compte/`
| URL | Vue | Description |
|---|---|---|
| `/compte/inscription/` | `inscription` | Créer un compte |
| `/compte/connexion/` | `connexion` | Se connecter |
| `/compte/deconnexion/` | `deconnexion` | Se déconnecter |
| `/compte/tableau-de-bord/` | `tableau_de_bord` | Dashboard vendeur |
| `/compte/profil/` | `profil` | Modifier son profil |
| `/compte/analytiques/` | `analytics_vendeur` | Graphiques de vues |
| `/compte/vendeur/<id>/` | `profil_vendeur` | Profil public d'un vendeur |
| `/compte/vendeur/<id>/avis/` | `laisser_avis` | Laisser un avis (POST) |

### Messagerie — `/messages/`
| URL | Vue | Description |
|---|---|---|
| `/messages/` | `inbox` | Boîte de réception |
| `/messages/<id>/` | `conversation` | Voir une conversation |
| `/messages/demarrer/<annonce_id>/` | `demarrer_conversation` | Initier un contact |

---

## API REST (Mobile)

Base URL : `/api/v1/`

Authentification : **JWT Bearer Token** — inclure dans les headers :
```
Authorization: Bearer <access_token>
```

Les tokens ont une durée de vie de **1 jour** (access) et **30 jours** (refresh).

### Authentification

| Méthode | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/inscription/` | Non | Créer un compte → retourne tokens + user |
| POST | `/api/v1/auth/connexion/` | Non | Login → retourne access + refresh tokens |
| POST | `/api/v1/auth/refresh/` | Non | Renouveler l'access token |
| GET/PUT | `/api/v1/auth/moi/` | Oui | Profil de l'utilisateur connecté |

**Exemple inscription :**
```json
POST /api/v1/auth/inscription/
{
  "email": "acheteur@example.com",
  "password": "motdepasse123",
  "first_name": "Mohammed",
  "last_name": "Alaoui",
  "telephone": "0661234567"
}
```

**Réponse :**
```json
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": { "id": 1, "first_name": "Mohammed", ... }
}
```

---

### Annonces

| Méthode | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/annonces/` | Non | Liste paginée (12/page) |
| GET | `/api/v1/annonces/<id>/` | Non | Détail + incrémente les vues |
| POST | `/api/v1/annonces/<id>/contacter/` | Oui | Envoyer un message au vendeur |

**Filtres disponibles sur la liste :**
```
?q=olivier           → recherche texte (titre, ville, description)
?region=marrakech    → filtrer par région
?type_culture=olivier
?prix_max=500000
?surface_min=5
?page=2
```

---

### Favoris

| Méthode | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/favoris/` | Oui | Mes annonces favorites |
| POST | `/api/v1/favoris/<id>/toggle/` | Oui | Ajouter ou retirer un favori |

**Réponse toggle :**
```json
{ "is_favori": true }
```

---

### Annonces du vendeur

| Méthode | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/mes-annonces/` | Oui | Mes annonces (tous statuts) |

---

### Profil vendeur

| Méthode | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/vendeurs/<id>/` | Non | Profil + annonces + avis |
| POST | `/api/v1/vendeurs/<id>/avis/` | Oui | Laisser un avis (note 1-5) |

**Condition pour laisser un avis :** avoir eu une conversation avec ce vendeur.

---

### Messagerie

| Méthode | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/conversations/` | Oui | Toutes mes conversations |
| GET | `/api/v1/conversations/<id>/messages/` | Oui | Messages + marque comme lus |

---

### Format de réponse — Annonce

```json
{
  "id": 42,
  "titre": "Terrain agricole 15ha — Marrakech",
  "region": "marrakech",
  "region_display": "Marrakech-Safi",
  "ville": "Chichaoua",
  "surface": "15.00",
  "prix": "750000.00",
  "prix_par_hectare": 50000,
  "type_culture": "olivier",
  "type_culture_display": "Olivier",
  "type_titre_foncier": "melkia",
  "acces_eau": true,
  "acces_route": true,
  "electricite": false,
  "latitude": "31.540000",
  "longitude": "-8.760000",
  "vues": 128,
  "statut": "active",
  "est_booste": false,
  "date_creation": "2025-03-15T10:30:00Z",
  "photo_principale": "http://localhost:8000/media/annonces/terrain.jpg",
  "vendeur": {
    "id": 5,
    "first_name": "Ahmed",
    "last_name": "Benali",
    "note_moyenne": 4.5,
    "nb_avis": 12
  }
}
```

---

## Application Mobile Flutter

### Statut actuel
- Flutter 3.32.4 installé
- Android Studio installé
- API REST Django prête à consommer
- Projet Flutter à créer (Phase 2 en cours)

### Architecture prévue
```
agrotech_mobile/
├── lib/
│   ├── main.dart
│   ├── core/
│   │   ├── api/           ← client HTTP + endpoints
│   │   ├── models/        ← Annonce, User, Message…
│   │   └── auth/          ← gestion JWT + stockage token
│   └── features/
│       ├── listings/      ← liste + détail terrain
│       ├── auth/          ← login + inscription
│       ├── favorites/     ← mes favoris
│       ├── messaging/     ← conversations
│       └── profile/       ← profil vendeur
└── pubspec.yaml
```

### Plateformes cibles
- Android (prioritaire)
- iOS (prévu — nécessite mise à jour macOS pour Xcode 26)
- Web Chrome (disponible immédiatement)

---

## Variables d'environnement

| Variable | Description | Exemple |
|---|---|---|
| `SECRET_KEY` | Clé secrète Django | `django-insecure-...` |
| `DEBUG` | Mode debug | `True` / `False` |
| `DB_NAME` | Nom de la base PostgreSQL | `agrotech` |
| `DB_USER` | Utilisateur PostgreSQL | `postgres` |
| `DB_PASSWORD` | Mot de passe PostgreSQL | `monmotdepasse` |
| `DB_HOST` | Hôte PostgreSQL | `localhost` |
| `DB_PORT` | Port PostgreSQL | `5432` |

---

## Commandes utiles

```bash
# Lancer le serveur de développement
python manage.py runserver

# Créer et appliquer les migrations
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Réinitialiser le mot de passe d'un utilisateur (shell)
python manage.py shell
>>> from accounts.models import User
>>> u = User.objects.get(email='exemple@email.com')
>>> u.set_password('nouveau_mot_de_passe')
>>> u.save()

# Vérifier la configuration Django
python manage.py check

# Collecter les fichiers statiques (production)
python manage.py collectstatic
```

---

## Roadmap

- [x] Phase 1 — Marketplace web (annonces, recherche, messagerie, favoris)
- [x] Phase 2 — Carte interactive Leaflet (GPS + fallback région)
- [x] Phase 3 — Analytiques vendeur, boost, comparaison, avis
- [x] Phase 4 — API REST Django (DRF + JWT + CORS)
- [ ] Phase 5 — Application mobile Flutter (Android)
- [ ] Phase 6 — iOS (après mise à jour macOS)
- [ ] Phase 7 — Paiement en ligne (boost), notifications push

---

*Dernière mise à jour : Juin 2026*
