# Figure out what version of centos, etc. to use
FROM centos:latest
LABEL Project=ecoHub Name=Aurora Version=0.0.1
WORKDIR /app
ADD . /app

# install yum requirements
RUN yum install -y centos-release-scl gcc
RUN yum install -y rh-python36

# create venv and install pip dependencies
RUN /opt/rh/rh-python36/root/usr/bin/python -m venv runner
RUN runner/bin/pip3 install -r requirements.txt

# run the eco_action script using venv on launch
ENTRYPOINT [ "python", "eco_action.py" ]

# add venv to path
ENV PATH="/app/runner/bin:${PATH}"

# local testing environment variables
