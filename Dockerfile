FROM python:3.11-slim

# Install system dependencies: tesseract-ocr, languages, and image libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set cloud environment variables
ENV PORT=7860
ENV STORAGE_DIR=/app/gate_cse_notes
RUN mkdir -p /app/gate_cse_notes

# Expose standard port
EXPOSE 7860

# Run uvicorn server dynamically using PORT environment variable
CMD ["sh", "-c", "python3 -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
