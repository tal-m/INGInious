FROM node:25-alpine

# Install grunt-cli globally
RUN npm install -g grunt-cli

WORKDIR /app

# Copy only package.json and package-lock.json first (for caching)
COPY package*.json ./scripts/minify/

# Install dependencies
WORKDIR /app/scripts/minify
RUN npm install

# Reset working dir to project root
WORKDIR /app

CMD ["grunt"]
