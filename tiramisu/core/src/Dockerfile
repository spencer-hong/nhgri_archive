FROM python:3.9.0-slim-buster
RUN apt-get -y update
RUN apt-get install -y --no-install-recommends libmagic1 netcat wget
ENV PYTHONPATH=/usr/lib/python3.9/site-packages

COPY src/requirements.txt /
RUN pip install -r /requirements.txt
# COPY src/*.whl /
# RUN pip install /*.whl
RUN rm /requirements.txt

# COPY context_dev /tiramisu

WORKDIR /app
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1