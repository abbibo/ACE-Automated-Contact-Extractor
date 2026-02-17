# Use specific Python version for reproducibility
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV/EasyOCR
# libgl1-mesa-glx is crucial for cv2
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a writable directory for EasyOCR model cache
# HF Spaces runs as user 1000, so we need to ensure permissions
RUN mkdir -p /app/.EasyOCR && \
    chmod 777 /app/.EasyOCR

# Set environment variable for EasyOCR to use the writable directory
ENV EASYOCR_MODULE_PATH=/app/.EasyOCR

# Expose port (Hugging Face Spaces defaults to 7860)
EXPOSE 7860

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
