# Figure out what version of centos, etc. to use
FROM centos:latest
LABEL Project=ecoHub Name=Aurora Version=0.0.1

# MongoDB (temporary demo solution)
RUN echo -e "\
[mongodb-org-4.2]\n\
name=MongoDB Repository\n\
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/4.2/x86_64/\n\
gpgcheck=1\n\
enabled=1\n\
gpgkey=https://www.mongodb.org/static/pgp/server-4.2.asc" >> /etc/yum.repos.d/mongodb-org-4.2.repo

RUN yum install -y mongodb-org

# install yum requirements
RUN yum install -y centos-release-scl gcc
RUN yum install -y rh-python36
RUN yum -y install initscripts

WORKDIR /app
ADD . /app

# install java 8
RUN yum install -y \
   java-1.8.0-openjdk \
   java-1.8.0-openjdk-devel

# set JAVA_HOME
ENV JAVA_HOME /usr/lib/jvm/java-1.8.0-openjdk/

# create venv and install pip dependencies
RUN /opt/rh/rh-python36/root/usr/bin/python -m venv runner
RUN runner/bin/pip3 install -r requirements.txt

# add venv to path
ENV PATH="/app/runner/bin:${PATH}"

# Temporarily hardcoded application variables
ENV MONGO_HOSTNAME=localhost
ENV MONGO_PORT=27017
#ENV KAFKA_HOSTNAME=ec2-3-215-226-109.compute-1.amazonaws.com
#ENV KAFKA_PORT=9092
#ENV KAFKA_INPUT_TOPIC=pipeline_input
#ENV KAFKA_OUTPUT_TOPIC=pipeline_output
ENV KAFKA_OFFSET_TOPIC=snow_offset

# local testing environment variables
ENV CONN="python -m snow.snow-table-parser.aurora_snow_connector"
ENV CONS="python -m snow.app.app"

# run the eco_action script using venv on launch
ENTRYPOINT [ "python", "eco_action.py" ]
