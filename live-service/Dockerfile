FROM node:22-alpine
WORKDIR /app

# Install from the committed lockfile so image builds are reproducible.
# Both files are needed by `npm ci`; copying only package.json would make
# every build re-resolve the dependency tree from the registry.
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY . .

# Don't run the server as root.
RUN addgroup -S app && adduser -S app -G app && chown -R app:app /app
USER app

ENV PORT=3000
EXPOSE 3000
CMD ["node", "server.js"]
