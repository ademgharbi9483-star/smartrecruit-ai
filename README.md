# SmartRecruit AI

Plateforme de recrutement avec analyse de CV assistée par IA : offres d'emploi, candidatures, extraction et scoring des CV, chatbot et notifications.

## Technologies

- **Backend** : Django 5.2, Django REST Framework, JWT, Celery (Redis), PostgreSQL
- **IA / NLP** : PyMuPDF (extraction de PDF), scikit-learn (scoring)
- **Frontend** : React 18, Vite, Tailwind CSS
- **Infrastructure** : Docker Compose, Nginx, n8n, GitHub Actions

## Structure

```
backend/    API Django (apps : authentication, candidates, jobs, ai_engine)
frontend/   Application React
nginx/      Configuration Nginx
n8n/        Workflows d'automatisation
```

## Configuration

Copier les fichiers d'exemple, puis adapter les valeurs :

```
copy .env.example .env
copy frontend\.env.example frontend\.env
```

Ne jamais publier les fichiers `.env`.

## Lancement local (sans Docker, avec SQLite)

Prérequis : Python 3.12, Node.js 20 ou plus.

Backend :

```
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:USE_SQLITE = "1"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 8000
```

Frontend (dans un second terminal) :

```
cd frontend
npm install
npm run dev
```

L'application est disponible sur http://localhost:3000.
Sans Redis ni Celery, les tâches asynchrones (analyse de CV, notifications) ne fonctionnent pas.

## Lancement complet avec Docker

```
docker compose up --build
```

L'application est servie par Nginx sur http://localhost:8090 (port défini par `NGINX_PORT`).

## Tests

```
cd backend
pip install -r requirements-dev.txt
$env:USE_SQLITE = "1"
python -m pytest tests/ --cov=apps
```