# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false
RUN poetry lock
RUN poetry install --no-interaction --no-ansi --without dev --no-root

# Copy source code
COPY src ./src

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "src/main.py"]
