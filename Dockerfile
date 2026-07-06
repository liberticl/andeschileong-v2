FROM python:3.11-slim
COPY requirements.txt /

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /andeschileong
WORKDIR /andeschileong
COPY . /andeschileong/

RUN apt-get update && apt-get install -y nginx wget tar && rm -rf /var/lib/apt/lists/*
ENV HUGO_VERSION 0.121.2
RUN wget -qO- https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_Linux-64bit.tar.gz | tar xz -C /usr/local/bin hugo

WORKDIR /andeschileong/hugo_site
RUN hugo --minify

WORKDIR /andeschileong
RUN mkdir -p /andeschileong/static
COPY nginx.conf /etc/nginx/nginx.conf
RUN python manage.py collectstatic --noinput --clear
RUN nginx -t

EXPOSE 80

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]