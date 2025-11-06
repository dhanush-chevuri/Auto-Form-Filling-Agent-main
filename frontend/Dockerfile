# Build stage
FROM node:20.18.0-alpine3.20 AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY . .
RUN npm run build

# Production stage with distroless
FROM gcr.io/distroless/nodejs20-debian12

WORKDIR /app
COPY --from=builder /app/build ./build
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

EXPOSE 3000
CMD ["npm", "start"]