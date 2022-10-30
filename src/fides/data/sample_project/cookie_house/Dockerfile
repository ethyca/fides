FROM node:16-alpine

ENV DATABASE_HOST localhost
ENV DATABASE_PORT 5432
ENV DATABASE_USER postgres
ENV DATABASE_PASSWORD postgres
ENV DATABASE_DB postgres_example

RUN mkdir /home/node/app
WORKDIR /home/node/app
COPY package.json package-lock.json ./
RUN npm clean-install
COPY . /home/node/app
RUN npm run build

EXPOSE 3000

ENV PORT 3000

CMD [ "npm", "run", "start" ]
