# Use a lightweight python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy codebase
COPY . .

# Expose Streamlit's default Cloud Run port
EXPOSE 8080

# Pre-run the workflow to generate necessary reports, then boot Streamlit
CMD ["sh", "-c", "python3 -m src.main && python3 -m streamlit run src/ui/dashboard.py --server.port 8080 --server.address 0.0.0.0"]
