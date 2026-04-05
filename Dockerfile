FROM python:3.12-slim

WORKDIR /app

# System deps for lxml, ffmpeg (whisperx audio decoding), and git (pip editable installs)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# Install uv for whisperx subprocess calls
RUN pip install --no-cache-dir uv

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install tribev2 as editable package
COPY tribev2/ tribev2/
RUN pip install  -e ./tribev2

# Copy application code
COPY main.py .
COPY service/ service/
COPY analysis_queue/ analysis_queue/
COPY router/ router/
COPY schema/ schema/
COPY tests/ tests/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
