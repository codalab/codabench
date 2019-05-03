FROM node:10

# Setup volume
VOLUME /app
WORKDIR /app

# Install packages
ADD package.json .
RUN npm install npm-watch stylus riot -g

CMD npm-watch
