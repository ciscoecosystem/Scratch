FROM centos:centos7.4.1708
LABEL Project=Tetration Name=PyGridAnnotations Version=0.0.1
WORKDIR /pygrid
ADD . /pygrid

# yum commands
RUN yum install -y centos-release-scl gcc
RUN yum install -y rh-python36
# install pip and then install dependencies
RUN /opt/rh/rh-python36/root/usr/bin/python -m venv pygrid_venv
RUN pygrid_venv/bin/pip3 install -r requirements.txt
# create log directory
RUN mkdir logs

# run the app when the container launches
ENTRYPOINT [ "pygrid_venv/bin/python", "pygrid.py" ]