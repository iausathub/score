ARG SETTINGS=score.settings.production
FROM --platform=linux/amd64 python:3.11

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

ARG SETTINGS
ENV SETTINGS_CONFIG=${SETTINGS}
ENV DJANGO_SETTINGS_MODULE=${SETTINGS}
RUN chmod +x /usr/src/app/start.sh
RUN chmod +x /usr/src/app/dev/kubernetes.sh
CMD /bin/bash -c "/usr/src/app/start.sh" ${SETTINGS_CONFIG}
