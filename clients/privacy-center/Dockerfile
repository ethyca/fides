# Based on vercel/next.js example https://github.com/vercel/next.js/blob/canary/examples/with-docker/Dockerfile

##############################
## Install the dependencies ##
##############################
FROM node:16-alpine as deps

RUN apk add --no-cache libc6-compat

WORKDIR /app

COPY package.json package-lock.json ./
COPY ./package.json ./package-lock.json ./

WORKDIR .
RUN npm clean-install


###########################
## Build the application ##
###########################
FROM node:16-alpine as builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build


##########################
## Setup the prod image ##
##########################
FROM node:16-alpine as runner

WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# We need to copy everything so we can rebuild with the new configs if needed
COPY --from=builder --chown=nextjs:nodejs /app .

# The config directory is not needed unless it is mounted as a volume because the next
# build has already been run. By deleteing it we can check if is was added with a volume
# and we to rebuild with a custom config.
RUN rm -r config

COPY ./start.sh .
RUN chmod +x start.sh && chown nextjs:nodejs start.sh

USER nextjs

EXPOSE 3000

CMD ["./start.sh"]
