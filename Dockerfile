# Stage 1: Install dependencies
FROM python:3.11-slim AS builder

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
# Using --no-cache-dir for smaller layers, --user to avoid permission issues if any
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Create a non-root user and group
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser

# Copy installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (assuming your code is in an 'app' subdirectory locally)
COPY ./app /app/app

# Switch to the non-root user
USER appuser

# Expose the port the application listens on (Cloud Run default is 8080)
# This is metadata; the application itself needs to listen on this port.
EXPOSE 8080

# Set the command to run the application
# Uvicorn will pick up the PORT environment variable from Cloud Run.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]