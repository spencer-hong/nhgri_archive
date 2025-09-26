FROM python:3.9.0-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1



RUN apt-get update \
    && pip install --upgrade pip setuptools wheel \
    # && pip install python-doctr[torch] \
    # && pip cache purge \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache/pip

COPY labelstudio/requirements.txt /
RUN pip install -r /requirements.txt

RUN rm /requirements.txt

RUN groupadd -g 1005 tiramisu 
RUN useradd -r -u 1005 -g tiramisu tiramisu

USER tiramisu

WORKDIR /app 
