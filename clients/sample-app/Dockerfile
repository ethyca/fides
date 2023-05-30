FROM node:16-alpine as prod

ENV FIDES_SAMPLE_APP__DATABASE_HOST localhost
ENV FIDES_SAMPLE_APP__DATABASE_PORT 5432
ENV FIDES_SAMPLE_APP__DATABASE_USER postgres
ENV FIDES_SAMPLE_APP__DATABASE_PASSWORD postgres
ENV FIDES_SAMPLE_APP__DATABASE_DB postgres_example

RUN mkdir /home/node/app
WORKDIR /home/node/app
COPY package.json package-lock.json ./
RUN npm clean-install
COPY . /home/node/app
RUN npm run build

EXPOSE 3000

ENV PORT 3000

CMD [ "npm", "run", "start" ]
