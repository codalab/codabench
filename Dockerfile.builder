FROM node:10

# Setup volume
VOLUME /app
WORKDIR /app

# Install packages
ADD package.json .
RUN npm install npm-watch -g
RUN npm install .

CMD npm-watch
