FROM python:3.8.3-alpine
EXPOSE 8081
WORKDIR /app
ADD . /app

COPY ./monitoring/pack /pack

RUN apk update \
    && apk upgrade \
    && apk add --no-cache -t dev build-base \
    && pip install -r /pack \
    && apk del dev \
    && adduser -u 1000 -D user


USER 1000

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8081", "monitoring.app:app"]