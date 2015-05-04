# Docker image for addressparser
# To build, run docker build --rm --tag=hmda/grasshopper-parser .
# A container can be started by running docker run -ti -p 5000:5000 hmda/grasshopper-parser

FROM ubuntu:latest
MAINTAINER Juan Marin Otero <juan.marin.otero@gmail.com>

RUN sudo apt-get update
RUN sudo apt-get -y install build-essential
RUN sudo apt-get -y install libtool
RUN sudo apt-get -y install autoconf
RUN sudo apt-get -y install python-setuptools
RUN sudo easy_install pip
RUN sudo apt-get -y install python python-dev python-setuptools libxml2-dev libxslt-dev zlib1g-dev
RUN sudo pip install usaddress
RUN sudo pip install flask

ADD ./app /docker/app

EXPOSE 5000

CMD ["python", "/docker/app/app.py"]
