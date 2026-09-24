FROM python:3.13-slim

# Install Node.js 24 and FFmpeg
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        ffmpeg \
    && curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && node --version \
    && npm --version \
    && ffmpeg -version \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -c "import yt_dlp; print('yt-dlp:', yt_dlp.version.__version__)" \
    && python -c "import yt_dlp_ejs; print('yt-dlp-ejs installed')"

EXPOSE 10000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]