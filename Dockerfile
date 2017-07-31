FROM gcr.io/google-appengine/python
MAINTAINER Jeremy L "jeremy212@gmail.com"

# Create a virtualenv for dependencies. This isolates these packages from
# system-level packages.
RUN virtualenv /env

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV PATH /env/bin:$PATH

# Copy the application's requirements.txt and run pip to install all
# dependencies into the virtualenv.
ADD . /app

RUN pip install -r /app/requirements.txt




# Run a WSGI server to serve the application. gunicorn must be declared as
# a dependency in requirements.txt.
CMD gunicorn -b :$PORT main:app


