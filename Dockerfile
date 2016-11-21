# Docker image for addressparser
# To build, run docker build --rm --tag=hmda/grasshopper-parser .
# A container can be started by running docker run -ti -p 5000:5000 hmda/grasshopper-parser

FROM python:2.7.9-onbuild
MAINTAINER Hans Keeler <hans.keeler@cfpb.gov>

USER daemon 

EXPOSE 5000

CMD ["gunicorn", "-c", "conf/gunicorn.py", "-b", "0.0.0.0:5000", "app:app"]
