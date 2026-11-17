FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev || npm install --omit=dev
COPY server.js .
EXPOSE 8080
CMD ["node", "server.js"]
