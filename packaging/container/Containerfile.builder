FROM node:lts-alpine3.23

# Setup volume
VOLUME /app
WORKDIR /app
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["npm install && export PATH=./node_modules/.bin:$PATH && npm-watch"]