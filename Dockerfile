# Dockerfile for Flask mortgage calculator API
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the complete application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (will be set by Render)
EXPOSE $PORT

# Run the API app with gunicorn
CMD ["gunicorn", "api_app:app", "--bind", "0.0.0.0:$PORT"]
