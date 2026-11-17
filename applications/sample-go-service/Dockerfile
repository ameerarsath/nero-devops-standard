# Multi-stage hermetic container build for Go 1.27.3 service
# Stage 1: Build static binary
FROM golang:alpine AS builder
WORKDIR /src
COPY go.mod ./
COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /app/service .

# Stage 2: Distroless minimal runtime with non-root UID 65532
FROM gcr.io/distroless/static-debian12:nonroot
USER nonroot:nonroot
WORKDIR /
COPY --from=builder /app/service /service
EXPOSE 8080
ENTRYPOINT ["/service"]
