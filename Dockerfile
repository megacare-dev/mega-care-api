# Use a builder image with Go installed
FROM golang:1.24 as builder

# Set the working directory
WORKDIR /app

# Copy the Go module files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy the source code
COPY *.go ./

# Build the application
# CGO_ENABLED=0 is important for static linking
# -o /app/helloworld specifies the output path and name
# -ldflags="-s -w" strips debug symbols, reducing binary size
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/helloworld .

# Use a minimal base image (like scratch or distroless)
# scratch is the smallest, but distroless provides some basic necessities
FROM gcr.io/distroless/static-debian11

# Set the working directory
WORKDIR /app
# Create a non-root user and group
RUN groupadd --system nonroot && \
    useradd --system --gid nonroot nonroot

# Copy the built binary from the builder stage
COPY --from=builder /app/helloworld /app/helloworld

# Switch to the non-root user
USER nonroot

# Expose the port the application listens on (Cloud Run default is 8080)
EXPOSE 8080

# Set the entrypoint to run the binary
ENTRYPOINT ["/app/helloworld"]