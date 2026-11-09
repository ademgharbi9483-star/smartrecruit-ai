# SmartRecruit AI — Documentation Technique du Sprint 1
## Explication détaillée du code pour les étudiants

**Projet :** SmartRecruit AI — Plateforme Intelligente de Recrutement Automatisé  
**Sprint :** 1 — Mise en place de l'architecture, Backend Django, Base de données, APIs Auth & Offres  
**Durée :** Semaines 1 et 2  
**Technologies :** Python 3.10, Django 4.2, Django REST Framework, PostgreSQL, JWT, Docker, Nginx

---

## Table des Matières

1. [Vue d'ensemble de ce qui a été réalisé](#1-vue-densemble)
2. [Structure du projet](#2-structure-du-projet)
3. [Infrastructure Docker](#3-infrastructure-docker)
4. [Configuration Django (settings.py)](#4-configuration-django)
5. [Modèles de Base de Données](#5-modèles-de-base-de-données)
6. [Module Authentification](#6-module-authentification)
7. [Module Offres d'Emploi](#7-module-offres-demploi)
8. [Système de Permissions](#8-système-de-permissions)
9. [Tests Unitaires](#9-tests-unitaires)
10. [CI/CD avec GitHub Actions](#10-cicd-avec-github-actions)
11. [Comment démarrer le projet](#11-comment-démarrer-le-projet)
12. [Récapitulatif des endpoints API](#12-récapitulatif-des-endpoints-api)

---

## 1. Vue d'ensemble

Durant ce Sprint 1, nous avons construit la **fondation complète** du backend de SmartRecruit AI. Voici ce qui a été réalisé :

| Réalisation | Fichier(s) |
|---|---|
| Structure du projet | Dossiers `backend/`, `frontend/`, `nginx/`, `n8n/` |
| Infrastructure Docker | `Dockerfile`, `docker-compose.yml`, `nginx.conf` |
| Configuration Django | `config/settings.py`, `config/urls.py`, `config/wsgi.py` |
| Modèle Utilisateur personnalisé | `apps/authentication/models.py` |
| Modèles BDD (Offre, CV, Candidature) | `apps/jobs/models.py`, `apps/candidates/models.py` |
| APIs Authentification complètes | `apps/authentication/views.py`, `serializers.py`, `urls.py` |
| APIs Offres d'emploi (CRUD) | `apps/jobs/views.py`, `serializers.py`, `filters.py`, `urls.py` |
| Système de permissions par rôle | `apps/authentication/permissions.py` |
| Tests unitaires | `tests/test_auth.py`, `tests/test_jobs.py` |
| Pipeline CI/CD | `.github/workflows/ci.yml` |

---

## 2. Structure du Projet

```
smart/                              ← Racine du projet
├── backend/                        ← Code Python/Django
│   ├── apps/                       ← Applications Django
│   │   ├── authentication/         ← Gestion des utilisateurs et auth
│   │   │   ├── models.py           ← Modèle User personnalisé
│   │   │   ├── serializers.py      ← Validation et transformation des données
│   │   │   ├── views.py            ← Logique des endpoints
│   │   │   ├── urls.py             ← Routes de l'app auth
│   │   │   ├── permissions.py      ← Règles d'accès par rôle
│   │   │   ├── admin.py            ← Interface d'administration
│   │   │   └── apps.py             ← Configuration de l'app
│   │   ├── jobs/                   ← Gestion des offres d'emploi
│   │   │   ├── models.py           ← Modèle JobOffer
│   │   │   ├── serializers.py      ← Validation des données offres
│   │   │   ├── views.py            ← Logique CRUD des offres
│   │   │   ├── urls.py             ← Routes de l'app jobs
│   │   │   ├── filters.py          ← Filtres de recherche avancés
│   │   │   └── admin.py
│   │   ├── candidates/             ← Gestion des CV et candidatures
│   │   │   └── models.py           ← Modèles CV, Application, CandidateProfile
│   │   └── ai_engine/              ← Module IA (développé au Sprint 5)
│   │       └── models.py           ← Logs des traitements IA
│   ├── config/                     ← Configuration centrale Django
│   │   ├── settings.py             ← Tous les paramètres du projet
│   │   ├── urls.py                 ← Routes principales
│   │   ├── wsgi.py                 ← Point d'entrée serveur web
│   │   └── celery.py               ← Configuration tâches asynchrones
│   ├── tests/                      ← Tests automatisés
│   │   ├── test_auth.py
│   │   └── test_jobs.py
│   ├── manage.py                   ← Commandes Django
│   ├── requirements.txt            ← Dépendances Python
│   └── pytest.ini                  ← Configuration des tests
├── nginx/
│   └── nginx.conf                  ← Configuration du reverse proxy
├── docker-compose.yml              ← Orchestration des services
├── .env.example                    ← Modèle de variables d'environnement
├── .gitignore                      ← Fichiers ignorés par Git
└── .github/workflows/ci.yml        ← Pipeline CI/CD
```

**Pourquoi cette structure ?**  
Django recommande d'organiser le code en "applications" (apps) indépendantes. Chaque app gère un domaine métier précis : `authentication` ne s'occupe que des utilisateurs, `jobs` ne s'occupe que des offres, etc. Cela facilite la maintenance, les tests, et la réutilisation du code.

---

## 3. Infrastructure Docker

### 3.1 Le Dockerfile (`backend/Dockerfile`)

Le Dockerfile est une recette qui décrit comment construire l'image Docker du backend.

```dockerfile
FROM python:3.10-slim
```
- `FROM` indique l'image de base. `python:3.10-slim` est une version légère de Python 3.10 (sans les outils inutiles pour la production).

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```
- `PYTHONDONTWRITEBYTECODE=1` : empêche Python de créer des fichiers `.pyc` (bytecode compilé) inutiles dans le conteneur.
- `PYTHONUNBUFFERED=1` : force Python à afficher les logs immédiatement dans le terminal (sans mise en tampon), ce qui est essentiel pour voir les logs Docker en temps réel.

```dockerfile
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*
```
- Installe les outils système nécessaires pour compiler `psycopg2` (le driver PostgreSQL pour Python). `rm -rf /var/lib/apt/lists/*` supprime le cache apt pour réduire la taille de l'image.

```dockerfile
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
```
- On copie d'abord seulement `requirements.txt` (avant le reste du code). Technique de **cache Docker** : si les dépendances n'ont pas changé, Docker réutilise le cache et ne réinstalle pas tout.

```dockerfile
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```
- `gunicorn` est un serveur WSGI de production (plus performant que le serveur de développement Django). `--workers 3` signifie 3 processus parallèles pour gérer les requêtes.

### 3.2 Le docker-compose.yml

Ce fichier orchestre **4 services** qui fonctionnent ensemble :

```yaml
services:
  db:          # PostgreSQL — la base de données
  backend:     # Django — l'API REST
  nginx:       # Le reverse proxy (point d'entrée unique)
  n8n:         # L'orchestrateur de workflows (pour les notifications)
```

**Le service `db` (PostgreSQL) :**
```yaml
db:
  image: postgres:15-alpine
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
    interval: 10s
    retries: 5
```
- `healthcheck` : Docker vérifie que PostgreSQL est prêt avant de démarrer le backend. Sans ça, le backend démarrerait avant que la base de données soit disponible et planterait.

**Le service `backend` (Django) :**
```yaml
backend:
  depends_on:
    db:
      condition: service_healthy   ← Attend que db soit healthy
  command: >
    sh -c "python manage.py migrate &&        ← Applique les migrations BDD
           python manage.py collectstatic &&   ← Regroupe les fichiers statiques
           gunicorn ..."                        ← Démarre le serveur
```

**Le service `nginx` (Reverse Proxy) :**  
Nginx est le point d'entrée unique. Il reçoit toutes les requêtes sur le port 80 et les redirige :
- `/api/` → vers Django (port 8000)
- `/media/` → vers les fichiers uploadés (CV des candidats)
- `/` → vers le frontend React (Sprint 3)

**Concept de Volume Docker :**
```yaml
volumes:
  postgres_data:   ← Les données de la BDD survivent aux redémarrages
  media_files:     ← Les CV uploadés sont partagés entre backend et nginx
```
Sans volumes, toutes les données seraient perdues à chaque redémarrage du conteneur.

### 3.3 La configuration Nginx (`nginx/nginx.conf`)

```nginx
upstream backend {
    server backend:8000;   ← "backend" est le nom du service Docker
}

location /api/ {
    proxy_pass http://backend;   ← Redirige vers Django
    proxy_set_header X-Real-IP $remote_addr;   ← Transmet la vraie IP du client
}

location /media/ {
    alias /app/media/;   ← Sert directement les fichiers sans passer par Django
}
```

**Pourquoi un reverse proxy ?**  
Nginx est très efficace pour servir des fichiers statiques et gérer les connexions réseau. Il libère Django pour se concentrer uniquement sur la logique métier.

---

## 4. Configuration Django

### 4.1 `config/settings.py` — Explication section par section

**Chargement des variables d'environnement :**
```python
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))
```
- `django-environ` lit le fichier `.env` et injecte les variables. On ne met **jamais** de mots de passe ou clés secrètes directement dans le code. C'est une règle de sécurité fondamentale.

**Organisation des applications installées :**
```python
DJANGO_APPS    = [...]   # Apps natives Django (admin, auth, etc.)
THIRD_PARTY_APPS = [...]  # Bibliothèques installées (DRF, JWT, etc.)
LOCAL_APPS     = [...]   # Nos propres applications

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
```
Cette organisation en 3 listes distinctes est une bonne pratique : on sait immédiatement quelle app vient d'où.

**Middleware (chaîne de traitement des requêtes) :**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Fichiers statiques en prod
    'corsheaders.middleware.CorsMiddleware',        # Gestion CORS (doit être HAUT)
    ...
]
```
Le middleware est une chaîne : chaque requête passe par tous ces composants dans l'ordre. `CorsMiddleware` doit être **très haut** dans la liste pour intercepter les requêtes CORS avant tout autre traitement.

**Configuration JWT :**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),    # Token valide 1h
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),        # Refresh valide 7j
    'ROTATE_REFRESH_TOKENS': True,                      # Nouveau refresh à chaque utilisation
    'BLACKLIST_AFTER_ROTATION': True,                   # L'ancien refresh est invalidé
}
```
- **Access Token** : durée courte (1h) pour limiter les risques si volé.
- **Refresh Token** : durée longue (7j) pour éviter de redemander le mot de passe.
- `ROTATE_REFRESH_TOKENS` : chaque utilisation du refresh génère un nouveau refresh, ce qui permet de détecter les vols de token.

**Configuration REST Framework :**
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',  # Par défaut, tout est protégé
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```
- En définissant `IsAuthenticated` par défaut, toutes les vues sont protégées. On utilise explicitement `AllowAny` pour les vues publiques (liste des offres, login, etc.).

---

## 5. Modèles de Base de Données

Un **modèle** Django est une classe Python qui représente une table dans PostgreSQL. Chaque attribut de classe est une colonne dans la table.

### 5.1 Modèle `User` (`apps/authentication/models.py`)

C'est le modèle le plus important. Django fournit un modèle User par défaut, mais on le remplace par un modèle personnalisé.

**Pourquoi personnaliser le modèle User ?**  
Le modèle Django par défaut utilise `username` comme identifiant. Dans SmartRecruit AI, on utilise l'**email** comme identifiant. On a aussi besoin d'un champ `role` (CANDIDAT, RECRUTEUR, ADMIN) qui n'existe pas par défaut.

```python
class User(AbstractBaseUser, PermissionsMixin):
```
- `AbstractBaseUser` : fournit les mécanismes de base (mot de passe hashé, authentification) sans imposer de champs spécifiques. Donne une liberté totale sur la structure.
- `PermissionsMixin` : ajoute le support des permissions Django (`is_staff`, `is_superuser`, groupes et permissions).

**Les rôles avec `TextChoices` :**
```python
class Role(models.TextChoices):
    CANDIDAT  = 'candidat',  'Candidat'
    RECRUTEUR = 'recruteur', 'Recruteur'
    ADMIN     = 'admin',     'Administrateur'
    #           ↑ valeur BDD   ↑ label affiché
```
`TextChoices` est une énumération Django. La valeur stockée en base est `'candidat'`, mais Django affiche `'Candidat'` dans les interfaces humaines. C'est plus lisible qu'une simple constante numérique.

**Le manager personnalisé :**
```python
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)   # "Test@GMAIL.com" → "test@gmail.com"
        user = self.model(email=email, **extra_fields)
        user.set_password(password)           # Hash le mot de passe avec bcrypt
        user.save(using=self._db)
        return user
```
Le `Manager` est la classe qui gère la création et la requête des objets. `normalize_email()` normalise l'email (minuscules sur la partie domaine). `set_password()` ne stocke **jamais** le mot de passe en clair — il le hash avec bcrypt automatiquement.

**Champs de réinitialisation du mot de passe :**
```python
reset_token         = models.CharField(max_length=255, blank=True, null=True)
reset_token_expires = models.DateTimeField(null=True, blank=True)
```
Quand un utilisateur demande à réinitialiser son mot de passe, on génère un token aléatoire qu'on stocke ici avec une date d'expiration. L'email envoyé contient ce token.

**Propriétés calculées :**
```python
@property
def is_candidat(self):
    return self.role == self.Role.CANDIDAT
```
Le décorateur `@property` transforme une méthode en attribut. On peut écrire `user.is_candidat` au lieu de `user.is_candidat()`. C'est utilisé partout dans les permissions.

**Configuration Django pour utiliser ce modèle :**
```python
# Dans settings.py
AUTH_USER_MODEL = 'authentication.User'
```
Cette ligne dit à Django d'utiliser notre modèle au lieu du modèle par défaut. Elle **doit** être définie avant la première migration.

### 5.2 Modèle `JobOffer` (`apps/jobs/models.py`)

```python
class JobOffer(models.Model):
    required_skills = models.JSONField(default=list)
```
`JSONField` stocke une liste Python (`["Python", "Django", "Docker"]`) directement en JSON dans PostgreSQL. C'est parfait pour les compétences car leur nombre est variable.

```python
recruiter = models.ForeignKey(
    settings.AUTH_USER_MODEL,  # Référence au modèle User
    on_delete=models.CASCADE,  # Si le recruteur est supprimé, ses offres aussi
    related_name='job_offers', # user.job_offers.all() pour accéder aux offres
)
```
- `ForeignKey` crée une relation "plusieurs-à-un" : un recruteur peut avoir plusieurs offres.
- `on_delete=models.CASCADE` : si on supprime un utilisateur, toutes ses offres sont supprimées automatiquement.
- `related_name='job_offers'` : permet d'écrire `recruteur.job_offers.all()` pour obtenir toutes les offres d'un recruteur.

**Méthode métier `auto_close_if_expired` :**
```python
def auto_close_if_expired(self):
    if self.is_expired() and self.status == self.Status.ACTIVE:
        self.status = self.Status.CLOSED
        self.save(update_fields=['status'])  # Update uniquement le champ 'status'
```
`save(update_fields=['status'])` est une optimisation importante : au lieu de mettre à jour toute la ligne en base, on ne met à jour que le champ `status`. C'est bien plus efficace sur de grandes tables.

### 5.3 Modèle `CV` (`apps/candidates/models.py`)

```python
def cv_upload_path(instance, filename):
    return f"cvs/user_{instance.candidate.id}/{filename}"
```
Cette fonction génère un chemin d'upload dynamique. Chaque candidat a son propre dossier : `media/cvs/user_42/mon_cv.pdf`. Cela évite les conflits de noms entre candidats.

```python
def validate_pdf(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext != '.pdf':
        raise ValidationError("Seuls les fichiers PDF sont acceptés.")
    if value.size > settings.MAX_CV_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"Le fichier ne doit pas dépasser {settings.MAX_CV_SIZE_MB} Mo.")
```
Validateur personnalisé appelé automatiquement par Django lors de l'upload. On vérifie l'extension ET la taille. La taille max est configurable via `settings.MAX_CV_SIZE_MB`.

```python
extracted_data = models.JSONField(default=dict)
# Structure attendue :
# {
#   "name": str, "email": str, "phone": str,
#   "skills": [...], "education": [...], "experience": [...]
# }
```
Ce champ JSON stockera les données extraites par le module IA au Sprint 5. On prépare la structure maintenant.

**Logique de CV principal :**
```python
def save(self, *args, **kwargs):
    if self.is_primary:
        # Enlève le statut "principal" de tous les autres CV du candidat
        CV.objects.filter(candidate=self.candidate, is_primary=True).update(is_primary=False)
    super().save(*args, **kwargs)
```
On surcharge la méthode `save()` pour garantir qu'un candidat n'a qu'un seul CV principal à la fois. Avant de sauvegarder, on remet à `False` tous les autres.

### 5.4 Modèle `Application` (Candidature)

```python
class Meta:
    unique_together = ('candidate', 'job_offer')  # Contrainte d'unicité
    ordering = ['-compatibility_score', '-applied_at']
```
- `unique_together` : empêche un candidat de postuler deux fois à la même offre au niveau base de données (contrainte d'intégrité).
- `ordering` : les candidatures sont triées par score décroissant puis par date. Le recruteur voit toujours les meilleurs candidats en premier.

```python
score_details = models.JSONField(default=dict)
# Exemple de valeur stockée :
# {
#   "skills_score": 85.5,
#   "experience_score": 70.0,
#   "matched_skills": ["Python", "Django"],
#   "missing_skills": ["Kubernetes"],
#   "summary": "Profil très compatible..."
# }
```
Ce champ sera rempli par le module IA au Sprint 5. On définit sa structure maintenant pour que les Sprints futurs aient un contrat clair.

---

## 6. Module Authentification

L'authentification suit le pattern **Serializer → View → URL** de Django REST Framework.

### 6.1 Les Sérialiseurs (`serializers.py`)

Un sérialiseur a deux rôles :
1. **Désérialisation** : valider et transformer les données JSON reçues → objet Python
2. **Sérialisation** : transformer un objet Python/Django → JSON à renvoyer au client

**`UserRegisterSerializer` :**
```python
class UserRegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
```
- `write_only=True` : ces champs sont acceptés en entrée mais **jamais renvoyés** en réponse. On ne renvoie jamais un mot de passe, même hashé.
- `validators=[validate_password]` : utilise les validateurs Django natifs (longueur minimum, pas trop commun, etc.).

```python
def validate(self, attrs):
    if attrs['password'] != attrs['password2']:
        raise serializers.ValidationError({"password": "Les deux mots de passe ne correspondent pas."})
    role = attrs.get('role', User.Role.CANDIDAT)
    if role == User.Role.ADMIN:
        raise serializers.ValidationError({"role": "..."})
    return attrs
```
La méthode `validate()` (sans suffixe de champ) est appelée après la validation individuelle de chaque champ. C'est là qu'on fait les validations **croisées** (ex: vérifier que password == password2).

```python
def create(self, validated_data):
    validated_data.pop('password2')       # On retire password2, pas un champ du modèle
    password = validated_data.pop('password')
    user = User(**validated_data)
    user.set_password(password)           # Hash le mot de passe
    user.save()
    return user
```
On surcharge `create()` pour gérer le hash du mot de passe. `set_password()` appelle bcrypt automatiquement.

**`CustomTokenObtainPairSerializer` — JWT enrichi :**
```python
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # On ajoute des données dans le payload du JWT
        token['email']     = user.email
        token['full_name'] = user.get_full_name()
        token['role']      = user.role
        return token
```
Le JWT est un token encodé en Base64. Son "payload" (partie centrale) contient des données appelées "claims". On y ajoute l'email, le nom et le rôle de l'utilisateur. Ainsi, le frontend peut lire ces informations directement depuis le token sans faire un appel API supplémentaire.

**`PasswordResetConfirmSerializer` — Vérification du token :**
```python
def validate(self, attrs):
    try:
        user = User.objects.get(reset_token=attrs['token'])
    except User.DoesNotExist:
        raise serializers.ValidationError({"token": "Token invalide ou expiré."})

    if user.reset_token_expires and user.reset_token_expires < timezone.now():
        raise serializers.ValidationError({"token": "Token expiré."})

    attrs['user'] = user   # On passe l'objet user aux données validées
    return attrs
```
On cherche l'utilisateur par son token, on vérifie l'expiration, et si tout est bon on **injecte l'objet user** dans les données validées. La vue récupérera cet user via `serializer.validated_data['user']`.

### 6.2 Les Vues (`views.py`)

**`RegisterView` — Inscription :**
```python
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]  # Pas besoin d'être connecté pour s'inscrire
    serializer_class   = UserRegisterSerializer
```
`generics.CreateAPIView` est une vue générique DRF qui gère automatiquement la méthode POST et appelle le sérialiseur. On n'a qu'à préciser quel sérialiseur utiliser.

**`LoginView` — Connexion JWT :**
```python
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
```
`TokenObtainPairView` est fourni par `djangorestframework-simplejwt`. On le surcharge juste pour utiliser notre sérialiseur personnalisé qui enrichit le JWT.

**`LogoutView` — Déconnexion (Blacklisting) :**
```python
def post(self, request):
    refresh_token = request.data.get("refresh_token")
    token = RefreshToken(refresh_token)
    token.blacklist()   # Invalide ce token dans la base de données
```
Le JWT est stateless par nature : une fois émis, il est valide jusqu'à expiration. Pour pouvoir "déconnecter" un utilisateur, on maintient une **liste noire** (blacklist) de tokens invalidés. `BLACKLIST_AFTER_ROTATION = True` dans les settings active cette fonctionnalité.

**`PasswordResetRequestView` — Sécurité anti-énumération :**
```python
generic_response = Response({"message": "Si cet email est enregistré..."})

try:
    user = User.objects.get(email=email)
except User.DoesNotExist:
    return generic_response  # Même réponse si l'email n'existe pas !
```
C'est une mesure de sécurité importante : si on répondait "Email introuvable", un attaquant pourrait tester des milliers d'emails pour savoir lesquels sont enregistrés (**énumération d'utilisateurs**). On renvoie toujours la même réponse.

```python
token = secrets.token_hex(32)   # 64 caractères hexadécimaux aléatoires
user.reset_token_expires = timezone.now() + timedelta(hours=1)
```
`secrets.token_hex(32)` génère un token **cryptographiquement sûr** de 64 caractères. Ne jamais utiliser `random` pour des tokens de sécurité.

**`ProfileView` — Profil :**
```python
class ProfileView(generics.RetrieveUpdateAPIView):
    def get_object(self):
        return self.request.user  # L'objet à modifier, c'est l'utilisateur connecté
```
`RetrieveUpdateAPIView` gère GET (lire), PUT (remplacer tout) et PATCH (modifier partiellement) automatiquement. En surchargeant `get_object()`, on dit que l'objet à lire/modifier est l'utilisateur connecté lui-même.

### 6.3 Les URLs (`urls.py`)

```python
urlpatterns = [
    path('register/',               RegisterView.as_view(),      name='auth-register'),
    path('login/',                  LoginView.as_view(),         name='auth-login'),
    path('logout/',                 LogoutView.as_view(),        name='auth-logout'),
    path('token/refresh/',          TokenRefreshView.as_view(),  name='token-refresh'),
    path('me/',                     me_view,                     name='auth-me'),
    path('profile/',                ProfileView.as_view(),       name='auth-profile'),
    path('change-password/',        ChangePasswordView.as_view(), name='auth-change-password'),
    path('password-reset/',         PasswordResetRequestView.as_view(), ...),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), ...),
]
```

Toutes ces URLs sont préfixées par `api/v1/auth/` dans `config/urls.py` :
```python
path('api/v1/auth/', include('apps.authentication.urls')),
```

Le préfixe `/v1/` permet de gérer des versions d'API : si on change l'API de manière incompatible, on crée `/v2/` sans casser les clients existants.

---

## 7. Module Offres d'Emploi

### 7.1 Trois Sérialiseurs pour un seul modèle

Une bonne pratique DRF : avoir des sérialiseurs différents selon le contexte.

```
JobOfferListSerializer      ← Utilisé pour GET /jobs/ (liste) — données allégées
JobOfferSerializer          ← Utilisé pour GET /jobs/<id>/ (détail) — données complètes
JobOfferCreateUpdateSerializer ← Utilisé pour POST/PUT/PATCH — données en entrée
```

**Pourquoi cette séparation ?**
- **Performance** : la liste n'a pas besoin de la description complète (longue). Moins de données = réponses plus rapides.
- **Sécurité** : le sérialiseur de création n'expose pas `recruiter` ou `id` (champs en lecture seule).
- **Clarté** : on contrôle précisément ce qu'on accepte en entrée vs ce qu'on retourne.

**Champs calculés avec `SerializerMethodField` :**
```python
recruiter_name     = serializers.SerializerMethodField(read_only=True)
applications_count = serializers.SerializerMethodField(read_only=True)

def get_recruiter_name(self, obj):
    return obj.recruiter.get_full_name()

def get_applications_count(self, obj):
    return obj.applications.count()
```
`SerializerMethodField` ajoute un champ calculé dynamiquement. La méthode associée doit commencer par `get_` suivi du nom du champ. Ces champs n'existent pas en base de données, ils sont calculés à la volée lors de la sérialisation.

**Validations croisées :**
```python
def validate(self, attrs):
    salary_min = attrs.get('salary_min')
    salary_max = attrs.get('salary_max')
    if salary_min and salary_max and salary_min > salary_max:
        raise serializers.ValidationError(
            {"salary_min": "Le salaire minimum ne peut pas dépasser le salaire maximum."}
        )
    return attrs
```
La méthode `validate()` vérifie la cohérence entre `salary_min` et `salary_max`. Ce type de validation implique plusieurs champs, donc elle va dans `validate()` et non dans `validate_salary_min()`.

### 7.2 Les Filtres (`filters.py`)

```python
class JobOfferFilter(django_filters.FilterSet):
    title    = django_filters.CharFilter(lookup_expr='icontains')
    location = django_filters.CharFilter(lookup_expr='icontains')
    salary_min = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
```

- `lookup_expr='icontains'` : recherche insensible à la casse qui contient le terme. Ex: `?title=python` trouvera "Développeur Python Senior".
- `lookup_expr='gte'` : "greater than or equal" (≥). `?salary_min=3000` retourne les offres avec un salaire min >= 3000.
- `lookup_expr='lte'` : "less than or equal" (≤). `?salary_max=5000` retourne les offres avec un salaire max <= 5000.

Usage : `GET /api/v1/jobs/?location=tunis&contract_type=CDI&salary_min=2000`

### 7.3 Les Vues (`views.py`)

**`JobOfferListView` — Performance avec `select_related` :**
```python
def get_queryset(self):
    # Étape 1 : auto-clôture des offres expirées
    expired_offers = JobOffer.objects.filter(
        status=JobOffer.Status.ACTIVE,
        expires_at__lt=timezone.now()
    )
    for offer in expired_offers:
        offer.auto_close_if_expired()

    # Étape 2 : retourner les offres actives
    return JobOffer.objects.filter(
        status=JobOffer.Status.ACTIVE
    ).select_related('recruiter')  # ← Optimisation SQL
```
`.select_related('recruiter')` fait un JOIN SQL pour charger le recruteur **en une seule requête** au lieu de faire N requêtes (une par offre). Sans ça, pour 20 offres, on ferait 21 requêtes SQL au lieu d'1 seule.

**`JobOfferCreateView` — Injection automatique du recruteur :**
```python
def perform_create(self, serializer):
    serializer.save(recruiter=self.request.user)  # Injecte l'utilisateur connecté
```
Le recruteur n'est **pas** fourni par le client (ce serait un risque de sécurité). Il est injecté automatiquement par le serveur à partir du token JWT de la requête.

**`JobOfferUpdateView` — Vérification de propriété :**
```python
def check_object_permissions(self, request, obj):
    if not request.user.is_admin and obj.recruiter != request.user:
        raise PermissionDenied("Vous ne pouvez modifier que vos propres offres.")
    super().check_object_permissions(request, obj)
```
On vérifie que le recruteur qui fait la requête est bien le propriétaire de l'offre. Un recruteur ne peut pas modifier les offres d'un autre recruteur.

**`job_stats_view` — Vue fonctionnelle avec `@api_view` :**
```python
@api_view(['GET'])
@permission_classes([AllowAny])
def job_stats_view(request):
    total  = JobOffer.objects.count()
    active = JobOffer.objects.filter(status=JobOffer.Status.ACTIVE).count()
    ...
    return Response({"total": total, "active": active, ...})
```
Pour les vues simples, on peut utiliser le décorateur `@api_view` au lieu de créer une classe. C'est plus concis pour des vues légères.

---

## 8. Système de Permissions

### `permissions.py` — Permissions personnalisées

DRF fournit `BasePermission` pour créer des règles d'accès sur mesure.

```python
class IsRecruteurOrAdmin(BasePermission):
    message = "Accès réservé aux recruteurs et administrateurs."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_recruteur or request.user.is_admin)
        )
```

**Deux niveaux de permission :**

1. `has_permission(request, view)` — Vérifié **avant** d'accéder à la vue. Ex: "Est-ce que cet utilisateur peut accéder à cette URL ?"

2. `has_object_permission(request, view, obj)` — Vérifié **sur un objet spécifique**. Ex: "Est-ce que cet utilisateur peut modifier **cette** offre en particulier ?"

```python
class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        # Flexible : supporte user, candidate, ou l'objet lui-même
        owner = getattr(obj, 'user', None) or getattr(obj, 'candidate', None) or obj
        return owner == request.user
```

`getattr(obj, 'user', None)` tente d'accéder à `obj.user`. Si l'attribut n'existe pas, retourne `None`. C'est une manière flexible de supporter plusieurs types d'objets (CV, Application, etc.).

**Utilisation dans les vues :**
```python
class JobOfferCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsRecruteurOrAdmin]
    # Django vérifie TOUTES les permissions de la liste (AND logique)
```

---

## 9. Tests Unitaires

### Philosophie des tests

Les tests vérifient que le code fait ce qu'on attend dans tous les cas : succès, erreurs, cas limites.

### `tests/test_auth.py`

**Les fixtures pytest :**
```python
@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def candidat_data():
    return {
        "email": "candidat@test.com",
        "password": "SecurePass123!",
        ...
    }
```
Une fixture est une fonction qui prépare des données réutilisables entre les tests. `APIClient()` est le client HTTP de test fourni par DRF — il simule des requêtes HTTP sans démarrer un vrai serveur.

**`@pytest.mark.django_db` :**
```python
@pytest.mark.django_db
class TestRegister:
    def test_register_candidat_success(self, api_client, candidat_data):
        response = api_client.post('/api/v1/auth/register/', candidat_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user']['email'] == candidat_data['email']
```
Ce décorateur autorise le test à accéder à la base de données. Pytest-django crée une base de données de test vide au début de chaque test et la détruit à la fin — les tests sont **isolés** et ne se polluent pas.

**Tests de cas d'erreur :**
```python
def test_register_password_mismatch(self, api_client, candidat_data):
    candidat_data['password2'] = 'WrongPassword!'
    response = api_client.post('/api/v1/auth/register/', candidat_data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST  # 400 = Bad Request
```
Il est aussi important de tester que le code **rejette** les données invalides que de tester qu'il accepte les données valides.

**Test de sécurité :**
```python
def test_register_admin_forbidden(self, api_client, candidat_data):
    candidat_data['role'] = 'admin'
    response = api_client.post('/api/v1/auth/register/', candidat_data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
```
On vérifie explicitement qu'un utilisateur ne peut pas s'attribuer le rôle admin lors de l'inscription.

### `tests/test_jobs.py`

**Fixtures chaînées :**
```python
@pytest.fixture
def auth_recruteur(api_client, recruteur):
    # Se connecte et configure le token dans le client
    response = api_client.post('/api/v1/auth/login/', {...})
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client  # Retourne un client déjà authentifié
```
La fixture `auth_recruteur` utilise elle-même les fixtures `api_client` et `recruteur`. C'est la **composition de fixtures** : on construit des scénarios complexes à partir de briques simples.

```python
api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
```
Cette ligne configure l'en-tête HTTP `Authorization: Bearer <token>` pour toutes les requêtes suivantes du client. C'est ainsi qu'un client authentifié envoie son token JWT.

**Test de contrôle d'accès :**
```python
def test_create_offer_as_candidat_forbidden(self, auth_candidat, offre_data):
    response = auth_candidat.post('/api/v1/jobs/create/', offre_data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN  # 403 = Interdit
```
On vérifie qu'un candidat (authentifié mais mauvais rôle) reçoit bien une erreur 403 et ne peut pas créer d'offre.

---

## 10. CI/CD avec GitHub Actions

### `.github/workflows/ci.yml`

```yaml
on:
  push:
    branches: [main, develop]   # Déclenché à chaque push sur main ou develop
  pull_request:
    branches: [main]             # Et à chaque PR vers main
```

**Le job `backend-tests` :**
```yaml
services:
  postgres:
    image: postgres:15-alpine    # Lance une vraie BDD PostgreSQL pour les tests
    env:
      POSTGRES_DB: smartrecruit_test
    options: >-
      --health-cmd pg_isready    # Attend que PostgreSQL soit prêt
      --health-interval 10s
```
GitHub Actions peut lancer des services Docker (comme PostgreSQL) pour les tests. Nos tests ont besoin d'une vraie base de données.

```yaml
steps:
  - uses: actions/checkout@v4           # Clone le code
  - uses: actions/setup-python@v5       # Installe Python 3.10
  - run: pip install -r requirements.txt # Installe les dépendances
  - run: python manage.py migrate       # Applique les migrations
  - run: pytest --cov=apps --cov-fail-under=70  # Lance les tests avec coverage
```

`--cov-fail-under=70` fait **échouer le pipeline** si la couverture de tests est inférieure à 70%. C'est une garantie de qualité automatique.

---

## 11. Comment Démarrer le Projet

### Prérequis
- Docker et Docker Compose installés
- Git installé

### Étapes

**1. Cloner le projet et configurer l'environnement :**
```bash
git clone <url-du-repo>
cd smart
cp .env.example .env
# Ouvrir .env et modifier les valeurs (mot de passe BDD, secret key, etc.)
```

**2. Démarrer tous les services :**
```bash
docker-compose up --build
```
La première fois, Docker télécharge les images et construit le backend. Les migrations sont appliquées automatiquement.

**3. Créer un superutilisateur admin :**
```bash
docker-compose exec backend python manage.py createsuperuser
```

**4. Accéder aux interfaces :**

| Interface | URL |
|---|---|
| API Documentation (Swagger) | http://localhost:8000/api/docs/ |
| Interface Admin Django | http://localhost:8000/admin/ |
| n8n (workflows) | http://localhost:5678 |
| API directe | http://localhost:8000/api/v1/ |

**5. Lancer les tests :**
```bash
docker-compose exec backend pytest
```

**6. Arrêter les services :**
```bash
docker-compose down            # Arrête mais conserve les données
docker-compose down -v         # Arrête ET supprime les volumes (données perdues)
```

---

## 12. Récapitulatif des Endpoints API

### Authentification (`/api/v1/auth/`)

| Méthode | Endpoint | Accès | Description |
|---|---|---|---|
| POST | `/register/` | Public | Inscription candidat ou recruteur |
| POST | `/login/` | Public | Connexion — retourne access + refresh token |
| POST | `/logout/` | Connecté | Déconnexion — invalide le refresh token |
| POST | `/token/refresh/` | Public | Obtenir un nouveau access token |
| GET | `/me/` | Connecté | Informations de l'utilisateur connecté |
| GET/PUT/PATCH | `/profile/` | Connecté | Consulter et modifier son profil |
| PUT | `/change-password/` | Connecté | Changer son mot de passe |
| POST | `/password-reset/` | Public | Demander un reset par email |
| POST | `/password-reset/confirm/` | Public | Confirmer le reset avec le token |

### Offres d'Emploi (`/api/v1/jobs/`)

| Méthode | Endpoint | Accès | Description |
|---|---|---|---|
| GET | `/` | Public | Liste des offres actives (avec filtres) |
| GET | `/stats/` | Public | Statistiques globales |
| GET | `/<id>/` | Public | Détail d'une offre |
| POST | `/create/` | Recruteur | Créer une offre |
| GET | `/my-offers/` | Recruteur | Ses propres offres |
| PUT/PATCH | `/<id>/update/` | Recruteur (propriétaire) | Modifier une offre |
| DELETE | `/<id>/delete/` | Recruteur (propriétaire) | Supprimer une offre |
| POST | `/<id>/close/` | Recruteur (propriétaire) | Clôturer une offre |

### Exemples de Requêtes

**Inscription :**
```json
POST /api/v1/auth/register/
{
    "email": "alice@gmail.com",
    "first_name": "Alice",
    "last_name": "Dupont",
    "role": "candidat",
    "password": "MonMotDePasse123!",
    "password2": "MonMotDePasse123!"
}
```

**Connexion :**
```json
POST /api/v1/auth/login/
{
    "email": "alice@gmail.com",
    "password": "MonMotDePasse123!"
}
```
Réponse :
```json
{
    "access": "eyJhbGciOiJIUzI1NiIs...",
    "refresh": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
        "id": 1,
        "email": "alice@gmail.com",
        "full_name": "Alice Dupont",
        "role": "candidat"
    }
}
```

**Requête authentifiée (Header obligatoire) :**
```
GET /api/v1/auth/me/
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Créer une offre d'emploi :**
```json
POST /api/v1/jobs/create/
Authorization: Bearer <token_recruteur>

{
    "title": "Développeur Python Senior",
    "description": "Description du poste...",
    "required_skills": ["Python", "Django", "Docker", "PostgreSQL"],
    "location": "Tunis",
    "contract_type": "CDI",
    "experience_level": "senior",
    "sector": "Informatique",
    "salary_min": 3000,
    "salary_max": 5000
}
```

**Filtrer les offres :**
```
GET /api/v1/jobs/?location=tunis&contract_type=CDI&salary_min=2000
GET /api/v1/jobs/?search=python
GET /api/v1/jobs/?ordering=-created_at
```

---

## Concepts Clés à Retenir

| Concept | Explication |
|---|---|
| **AbstractBaseUser** | Permet de créer un modèle User totalement personnalisé en Django |
| **JWT** | Token signé qui contient des informations sur l'utilisateur, sans état serveur |
| **Blacklisting** | Technique pour invalider un JWT avant son expiration naturelle |
| **SerializerMethodField** | Champ calculé dynamiquement dans un sérialiseur DRF |
| **select_related()** | Optimisation Django qui évite le problème N+1 avec les relations FK |
| **@pytest.fixture** | Données ou objets réutilisables entre plusieurs tests |
| **Docker Volume** | Persistance des données entre redémarrages de conteneurs |
| **Reverse Proxy** | Nginx reçoit les requêtes et les redirige vers le bon service |
| **Anti-énumération** | Répondre toujours la même chose pour ne pas révéler l'existence d'un compte |
| **unique_together** | Contrainte d'unicité sur plusieurs colonnes en base de données |

---

*Document rédigé dans le cadre du Projet de Fin d'Études — SmartRecruit AI — Année universitaire 2024-2025*
