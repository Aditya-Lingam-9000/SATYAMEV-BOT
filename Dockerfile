# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /code

# Install system dependencies required for OpenCV, EasyOCR, and Audio processing
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    fonts-freefont-ttf \
    fonts-deva \
    fonts-telu \
    fonts-taml \
    fonts-beng \
    && rm -rf /var/lib/apt/lists/*


# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create cache directory for EasyOCR and Hugging Face and make it writable for user 1000 (Hugging Face default)
RUN mkdir -p /.cache && chmod -R 777 /.cache

# Expose port 7860 (Hugging Face Spaces default)
EXPOSE 7860

# Command to run the application using Uvicorn
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "7860"]
