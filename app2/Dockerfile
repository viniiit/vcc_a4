FROM gcc:latest
COPY server.c /app/server.c
WORKDIR /app
RUN gcc -o server server.c
CMD ["./server"]

