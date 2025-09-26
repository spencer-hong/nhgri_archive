FROM python:3.9.0-slim-buster
RUN apt-get -y update
ENV PYTHONPATH=/usr/lib/python3.9/site-packages


RUN python -m pip install --upgrade pip 
COPY neo4j_tasks/requirements.txt /
RUN pip install -r /requirements.txt

RUN rm /requirements.txt
WORKDIR /app

RUN pip cache purge \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache/pip

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1