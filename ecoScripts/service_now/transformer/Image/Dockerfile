# Figure out what version of centos, etc. to use
FROM centos:centos7
LABEL Project=ecoHub Name=Aurora Version=0.0.1


#RUN yum install -y mongodb-org

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

# run the eco_action script using venv on launch
ENTRYPOINT [ "python", "eco_action.py" ]
