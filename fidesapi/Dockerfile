##########
# Local image for development
ARG OPENJDK_TAG=11-jre-buster

FROM openjdk:${OPENJDK_TAG} as local

# Install SBT
ARG SBT_VERSION=1.4.9
RUN \
    mkdir /working/ && \
    cd /working/ && \
    curl -L -o sbt-$SBT_VERSION.deb https://repo.scala-sbt.org/scalasbt/debian/sbt-$SBT_VERSION.deb && \
    dpkg -i sbt-$SBT_VERSION.deb && \
    rm -r /working

# Copy Local Files
WORKDIR /usr/src/fidesapi
COPY project project/
COPY build.sbt .
# TODO: ideally, this wouldn't be needed to run sbt update
COPY src/main/resources/reference.conf src/main/resources/reference.conf
RUN sbt update
EXPOSE 8080
