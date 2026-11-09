# ── SmartRecruit AI — Frontend Dockerfile (multi-stage) ─────────────────────

# ── Étape 1 : Build React ────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Copier les fichiers de dépendances d'abord (cache layer)
COPY package.json ./

# Installer les dépendances
RUN npm install

# Copier le reste du code source
COPY . .

# Variables d'environnement pour le build
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

# Build de production
RUN npm run build

# ── Étape 2 : Servir avec Nginx ──────────────────────────────────────────────
FROM nginx:1.25-alpine AS production

# Copier le build React
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuration Nginx intégrée au frontend (SPA routing)
RUN echo 'server { \
    listen 3000; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
