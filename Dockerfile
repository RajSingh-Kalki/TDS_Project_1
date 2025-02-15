FROM python:3.12-slim-bookworm

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git

# Download and install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Install FastAPI, Uvicorn, and Pillow
RUN pip install fastapi uvicorn Pillow

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin:$PATH"

# Set up the application directory
WORKDIR /app

# Copy application files
COPY main.py /app
COPY tasks.py /app

# Explicitly set the correct binary path and use `sh -c`
CMD ["sh", "-c", "/root/.local/bin/uv run app.py"]
