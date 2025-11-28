FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requriements.txt .
RUN pip install --no-cache-dir -r requriements.txt
RUN pip install gunicorn

# Copy project
COPY . .

# Set working directory to where manage.py is located
WORKDIR /app/bizai

# Collect static files (optional, can be done in entrypoint)
# RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Default command (overridden by docker-compose)
CMD ["gunicorn", "bizai.wsgi:application", "--bind", "0.0.0.0:8000"]
