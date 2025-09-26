FROM python:3.9.0-slim-buster
RUN apt-get -y update
RUN apt-get install -y --no-install-recommends libmagic1 netcat wget

# required for java runtime
RUN mkdir -p /usr/share/man/man1 /usr/share/man/man2

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jre

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get -y install \
    libreoffice-common \ 
    libreoffice-java-common \
    libreoffice-writer \
    hyphen-af hyphen-en-us \
    fonts-dejavu fonts-dejavu-core fonts-dejavu-extra \
    fonts-droid-fallback fonts-dustin fonts-f500 fonts-fanwood fonts-freefont-ttf fonts-liberation \
    fonts-lmodern fonts-lyx fonts-sil-gentium fonts-texgyre fonts-tlwg-purisa fonts-opensymbol && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/usr/lib/python3.9/site-packages

RUN python -m pip install --upgrade pip 
RUN python -m pip install --upgrade pymupdf

RUN pip install unoserver

COPY digest/requirements.txt /
RUN pip install -r /requirements.txt
COPY rust/target/wheels/*.whl /
RUN pip install /*.whl
RUN rm /requirements.txt
RUN rm /*.whl

RUN pip cache purge \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache/pip

# COPY context_dev /tiramisu

WORKDIR /app
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1