FROM python:3.7.9

ENV PYTHONUNBUFFERED=0

RUN pip install pip \
 && pip install nox \
 && pip install pre-commit

WORKDIR /pdbr
COPY . .

RUN pre-commit run --all-files
RUN nox --sessions test django_test
