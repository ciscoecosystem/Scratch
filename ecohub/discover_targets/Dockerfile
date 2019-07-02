FROM centos:centos7.4.1708
LABEL Project=ecoHub Name=Target_Connectivity Version=0.0.1
WORKDIR /app
ADD . /app

# install yum requirements
RUN yum install -y centos-release-scl gcc
RUN yum install -y rh-python36

# create venv and install pip dependencies
RUN /opt/rh/rh-python36/root/usr/bin/python -m venv runner
RUN runner/bin/pip3 install -r requirements.txt

# run the eco_action script using venv on launch
ENTRYPOINT [ "runner/bin/python", "eco_action.py" ]