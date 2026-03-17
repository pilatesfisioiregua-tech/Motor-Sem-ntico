FROM python:3.12-slim

# System deps for git, document parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (cached layer)
COPY motor-semantico/motor_v1_validation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Code OS v2 agent code
COPY motor-semantico/motor_v1_validation/agent/ /app/

# Copy full repo for project file access
COPY . /repo/

EXPOSE 8080

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV CODE_OS_PROJECT_DIR=/repo

CMD ["python", "api.py"]
