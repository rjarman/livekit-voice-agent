FROM node:20-alpine AS builder

WORKDIR /app

# Build argument from docker-compose (required)
ARG VITE_SERVER_IP_ADDRESS
ENV VITE_SERVER_IP_ADDRESS=$VITE_SERVER_IP_ADDRESS

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files to nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
