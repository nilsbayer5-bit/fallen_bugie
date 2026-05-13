# /home/nils/fallen_bugie/frontend/Dockerfile
# Phase 1: Bauen (Node.js)
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

# Phase 2: Ausliefern (Nginx)
FROM nginx:alpine
# Kopiere das fertige Build in den Nginx Web-Ordner
COPY --from=builder /app/dist /usr/share/nginx/html
# Port 80 freigeben
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]