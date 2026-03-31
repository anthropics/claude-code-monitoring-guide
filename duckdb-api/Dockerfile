FROM golang:1.25-bookworm AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=1 go build -o duckdb-api .

FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/duckdb-api /usr/local/bin/duckdb-api

RUN mkdir -p /data/lifecycle

EXPOSE 8082

CMD ["duckdb-api"]
