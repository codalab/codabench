FROM node:10

# Setup volume
VOLUME /app
WORKDIR /app

# Install packages
ADD package.json .
RUN npm install npm-watch stylus riot@3.13.2 -g

CMD npm-watch
