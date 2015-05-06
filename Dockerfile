# Docker image for addressparser
# To build, run docker build --rm --tag=hmda/grasshopper-parser .
# A container can be started by running docker run -ti -p 5000:5000 hmda/grasshopper-parser

FROM python:2.7.9-onbuild
MAINTAINER Juan Marin Otero <juan.marin.otero@gmail.com>

EXPOSE 5000

CMD ["python", "./app/app.py"]
