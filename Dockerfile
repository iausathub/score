FROM --platform=linux/amd64 python:3.11

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

RUN chmod +x /usr/src/app/start.sh
CMD ["/usr/src/app/start.sh"]
