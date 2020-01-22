FROM python:3-slim
COPY ./ /app/
WORKDIR /app
RUN apt-get -qq update
RUN apt-get install -y curl gnupg
RUN curl -sL https://deb.nodesource.com/setup_9.x | bash -
RUN apt-get install -y nodejs
RUN npm install -g gulp
RUN echo "1" > VERSION
RUN rm -r .git
RUN python uranium
CMD ["python", "/app/bin/gunicorn", "main:app", "-c", "gunicorn_config.py"]
