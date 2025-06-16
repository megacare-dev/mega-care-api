# Stage 1: Build the application
FROM node:20-alpine AS builder

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install dependencies, including devDependencies for building
RUN npm install

# Copy tsconfig.json
COPY tsconfig.json ./

# Copy the rest of the application source code
COPY . .

# Build TypeScript to JavaScript
RUN npm run build

# Prune devDependencies for the final image
RUN npm prune --production

# Stage 2: Create the production image
FROM node:20-alpine

# Set the working directory
WORKDIR /app

# Create a non-root user and group
RUN addgroup --system nonroot && \
    adduser --system --ingroup nonroot nonroot

# Copy built application (dist folder) and production node_modules from builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./

# Switch to the non-root user
USER nonroot

# Expose the port the application listens on (Cloud Run default is 8080)
# This is metadata; the application itself needs to listen on this port.
EXPOSE 8080

# Set the command to run the application
CMD ["node", "dist/server.js"]