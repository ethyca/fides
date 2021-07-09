##########
# Local image for development
FROM adoptopenjdk:8-jre-hotspot as local
RUN apt-get update
RUN apt-get install -y \
    gnupg \
    vim

# Install SBT
ARG SBT_VERSION=1.4.9
RUN echo "deb https://dl.bintray.com/sbt/debian /" | tee -a /etc/apt/sources.list.d/sbt.list
RUN curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | apt-key add
RUN apt-get update
RUN apt-get install -y sbt=$SBT_VERSION -V

# Copy Local Files
WORKDIR /usr/src/fides-server
COPY project project/
COPY build.sbt .
# TODO: ideally, this wouldn't be needed to run sbt update
COPY src/main/resources/reference.conf src/main/resources/reference.conf
RUN sbt update
EXPOSE 8080

##########
# Build image to compile
FROM local as build
WORKDIR /usr/src/fides-server
COPY src src/
RUN sbt package

##########0
# Production image, including just the JRE
FROM adoptopenjdk:8-jre-hotspot as production
# TODO: parameterize this intelligently with args?
COPY --from=build /usr/src/fides-server/target/scala-2.12/fides-server_2.12-0.1.0-SNAPSHOT.war /usr/fides-server/fides-server.war
COPY --from=build /usr/src/fides-server/src/main/resources/logback.xml /usr/fides-server/logback.xml
COPY deploy/jetty-runner-9.4.34.v20201102.jar /usr/fides-server/jetty-runner.jar
EXPOSE 8080

CMD java -Dlogback.configurationFile='/usr/fides-server/logback.xml' -jar /usr/fides-server/jetty-runner.jar /usr/fides-server/fides-server.war
