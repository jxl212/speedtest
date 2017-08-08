FROM python:alpine
MAINTAINER Jeremy L "jeremy212@gmail.com"

ADD . /app

RUN pip install virtualenv
WORKDIR /app
RUN virtualenv .env/
RUN source .env/bin/activate
# Setting these environment variables are the same as running
ENV PATH ./env/bin:$PATH
RUN pip install -r /app/requirements.txt

# Run a WSGI server to serve the application. gunicorn must be declared as
# a dependency in requirements.txt.
CMD gunicorn -b :$PORT main:app --reload
