# Use an official Python runtime as a parent image
FROM python:3.12.4-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  git \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${PATH}:/root/.local/bin"

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock* /app/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Copy project
COPY . /app

# Install grep-ast from GitHub
RUN poetry run pip install git+https://github.com/paul-gauthier/grep-ast.git

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "python", "-m", "src.reporag.main"]