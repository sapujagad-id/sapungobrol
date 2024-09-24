# Build stage
FROM python:3.11.3-slim-buster AS build

WORKDIR /app

# Install dependencies and activate env
RUN set -ex && apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/* && \
    python -m venv env

ENV PATH="env/bin:$PATH"

# Copy requirements and install
COPY ./requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Runner stage
FROM python:3.11.3-slim-buster AS run

WORKDIR /app

# Install dependencies and remove package lists
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy virtual env to runner and activate
COPY --from=build /app/env /app/env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONBUFFERED=1 \
    PATH="env/bin:$PATH"

# Copy project
COPY . .

# Expose port 8000
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "python main.py"]