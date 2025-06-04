# Production Frontend Dockerfile for React application
FROM node:18-alpine as build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY src/ ./src/
COPY public/ ./public/
COPY webpack.config.js ./
COPY tsconfig.json ./
COPY .babelrc ./

# Build production bundle
RUN npm run build

# Production nginx stage
FROM nginx:alpine as production

# Copy built app to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.frontend.conf /etc/nginx/conf.d/default.conf

# Create nginx user and set permissions
RUN addgroup -g 1001 -S karen && \
    adduser -S karen -u 1001 && \
    chown -R karen:karen /var/cache/nginx && \
    chown -R karen:karen /var/log/nginx && \
    chown -R karen:karen /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R karen:karen /var/run/nginx.pid

# Switch to non-root user
USER karen

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]