FROM python:3.12-slim

# Install ffmpeg and tzdata for timezone support
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency file and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY config.py main.py ./

# Create directory for saved images
RUN mkdir -p /app/saved_images

# Run the application
CMD ["python", "main.py"]

