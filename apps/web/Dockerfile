
# Development image for the Jyotish web app
FROM node:22-alpine

RUN corepack enable

WORKDIR /app

# Install dependencies first for better Docker caching
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

# Copy the application code
COPY . .

EXPOSE 3000

# Start Next.js and allow access from outside the container
CMD ["pnpm", "dev", "--hostname", "0.0.0.0"]
