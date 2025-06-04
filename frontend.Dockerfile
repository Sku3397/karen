# Frontend Dockerfile for React application
FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY src/ ./src/
COPY public/ ./public/
COPY webpack.config.js ./
COPY tsconfig.json ./
COPY .babelrc ./

# Development target
FROM base as development
EXPOSE 3000
CMD ["npm", "start"]

# Production build target
FROM base as build
RUN npm run build

# Production target with nginx
FROM nginx:alpine as production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.frontend.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]