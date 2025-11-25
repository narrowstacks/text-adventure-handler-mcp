# Build frontend
FROM oven/bun:1-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/bun.lock* ./
RUN bun install --frozen-lockfile
COPY frontend/ .
RUN bun run build

# Build backend
FROM oven/bun:1-alpine AS backend-builder
WORKDIR /app/backend
COPY backend/package.json backend/bun.lock* ./
RUN bun install --frozen-lockfile
COPY backend/ .
RUN bun run build

# Final image with nginx + bun
FROM oven/bun:1-alpine

# Install nginx and supervisor
RUN apk add --no-cache nginx supervisor

# Copy frontend build to nginx
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Copy backend build
WORKDIR /app
COPY --from=backend-builder /app/backend/dist ./dist
COPY --from=backend-builder /app/backend/node_modules ./node_modules
COPY --from=backend-builder /app/backend/package.json ./

# Nginx config - proxy /api to backend on localhost
RUN mkdir -p /etc/nginx/http.d
COPY <<'EOF' /etc/nginx/http.d/default.conf
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Supervisor config to run both services
COPY <<'EOF' /etc/supervisord.conf
[supervisord]
nodaemon=true
logfile=/dev/null
logfile_maxbytes=0

[program:nginx]
command=nginx -g "daemon off;"
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:backend]
command=bun /app/dist/index.js
directory=/app
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=DB_PATH="%(ENV_DB_PATH)s"
EOF

EXPOSE 80

CMD ["supervisord", "-c", "/etc/supervisord.conf"]
