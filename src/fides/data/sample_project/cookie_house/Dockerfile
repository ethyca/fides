FROM node:16-alpine

USER root

RUN mkdir /home/node/app
WORKDIR /home/node/app
COPY package.json package-lock.json ./
RUN npm clean-install
COPY . /home/node/app
RUN npm run build

EXPOSE 3000

ENV PORT 3000

CMD [ "npm", "run", "start" ]
