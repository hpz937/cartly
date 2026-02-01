FROM python:3.12-alpine

WORKDIR /app

# System deps for Pillow and clean installs
RUN apk add --no-cache jpeg zlib libwebp && \
    apk add --no-cache --virtual .build-deps gcc musl-dev jpeg-dev zlib-dev libwebp-dev && \
    pip install --no-cache-dir gunicorn flask Pillow && \
    apk del .build-deps

COPY app.py .

# Persistent SQLite lives here
VOLUME /app/data

EXPOSE 5000

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
