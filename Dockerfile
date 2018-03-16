FROM pypy:3-slim
COPY ./ /app/
WORKDIR /app
RUN ls
RUN "pypy3 uranium"
CMD ["./bin/pypy3"]
