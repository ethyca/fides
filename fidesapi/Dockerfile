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

##########
# Build image to compile
FROM local as build
WORKDIR /usr/src/fidesapi
COPY src src/
RUN sbt package

##########0
# Production image, including just the JRE
FROM openjdk:${OPENJDK_TAG}
# TODO: parameterize this intelligently with args?
COPY --from=build /usr/src/fidesapi/target/scala-2.12/fidesapi_2.12-0.1.0-SNAPSHOT.war /usr/fidesapi/fidesapi.war
COPY --from=build /usr/src/fidesapi/src/main/resources/logback.xml /usr/fidesapi/logback.xml
COPY deploy/jetty-runner-9.4.34.v20201102.jar /usr/fidesapi/jetty-runner.jar
EXPOSE 8080

CMD java -Dlogback.configurationFile='/usr/fidesapi/logback.xml' -jar /usr/fidesapi/jetty-runner.jar /usr/fidesapi/fidesapi.war
