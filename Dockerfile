FROM python:3.7.9

ENV PYTHONUNBUFFERED=0

RUN pip install pip \
 && pip install nox

WORKDIR /pdbr
COPY . .

RUN nox --sessions check
RUN nox --sessions test
