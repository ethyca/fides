FROM node:alpine

USER root

RUN mkdir /home/node/app
WORKDIR /home/node/app
COPY package.json package.json
RUN npm install
COPY . /home/node/app
RUN npm run build

EXPOSE 3000

ENV PORT 3000

CMD [ "npm", "run", "start" ]
