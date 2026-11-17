# Node.js runtime for the Next.js dev server; bun is only the package manager
FROM node:26-alpine

# Bun binary (musl build) for installs; bun.lock is the only lockfile
COPY --from=oven/bun:1.4.4-alpine /usr/local/bin/bun /usr/local/bin/bun

# Set working directory
WORKDIR /app

# Install dependencies exactly as locked
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# Copy application code
COPY . .

# Accept build arguments
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

# Disable telemetry
ENV NEXT_TELEMETRY_DISABLED=1

# Expose port 3000
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Run the development server with hot reload (next runs on Node via its shebang)
CMD ["bun", "run", "dev"]
