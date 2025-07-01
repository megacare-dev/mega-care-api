# Stage 1: Builder & Tester
# This stage installs all dependencies into a virtual environment and runs tests.
FROM python:3.11-slim as builder

WORKDIR /app

# Set environment variables to prevent Python from writing .pyc files and to buffer output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Define the location for the virtual environment
ENV VIRTUAL_ENV=/opt/venv

# Create a virtual environment
RUN python3 -m venv $VIRTUAL_ENV

# Add the virtual environment to the PATH
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies
# Copying requirements.txt first leverages Docker's layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Run unit tests. The build will fail if tests do not pass.
RUN pytest

# Stage 2: Production
# This stage creates the final, lean production image.
FROM python:3.11-slim as production

WORKDIR /app

# Create a non-root user for security
RUN addgroup --system app && adduser --system --group app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
COPY ./app ./app

# Set the path to include the venv and switch to the non-root user
ENV PATH="/opt/venv/bin:$PATH"
RUN chown -R app:app /app
USER app

# Expose the port the app will run on. Cloud Run uses port 8080 by default.
EXPOSE 8080

# Run the application using Gunicorn with Uvicorn workers for production
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8080"]