FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
# Build dependencies needed for sqlite3 native module
RUN apk add --no-cache python3 make g++ sqlite && \
    npm install --production

COPY server.js ./

EXPOSE 8081

CMD ["npm", "start"]
