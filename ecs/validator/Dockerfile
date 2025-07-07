
# # Base image with Python 3.11
# FROM python:3.11-slim

# # Set environment variables
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# # Set working directory
# WORKDIR /app

# # Install system dependencies
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends gcc build-essential && \
#     rm -rf /var/lib/apt/lists/*

# # Install Python dependencies
# COPY requirements.txt .
# RUN pip install --upgrade pip && pip install -r requirements.txt

# # Copy your script and .env
# COPY validator.py .
# COPY .env .

# # Run the script
# CMD ["python", "validator.py"]



# Base image with Python 3.11
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your script only (no .env)
COPY validator.py .

# Run the script
CMD ["python", "validator.py"]
