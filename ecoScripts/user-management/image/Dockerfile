FROM centos:centos7.4.1708
LABEL Project=Runner Name=ActiveDirectory-Actions Version=0.1
WORKDIR /app
ADD . /app/

# install pip and then install dependencies
RUN curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
RUN python get-pip.py
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# install acitoolkit
RUN yum install -y git python-devel gcc
RUN git clone https://github.com/datacenter/acitoolkit \
  && cd acitoolkit \
  && python setup.py install

# remove unneeded files
RUN rm -f requirements.txt
RUN rm -f get-pip.py
RUN rm -Rf acitoolkit/

# run the app when the container launches
# ENTRYPOINT [ "/bin/bash" ]
ENTRYPOINT [ "python", "eco_action.py" ]