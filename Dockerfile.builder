FROM node:10

# Setup volume
VOLUME /app
WORKDIR /app

# Install packages
ADD package.json .

RUN npm install

CMD export PATH=./node_modules/.bin:$PATH && npm-watch
