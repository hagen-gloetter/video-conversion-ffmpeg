FROM ubuntu:24.04

LABEL maintainer="Hagen Glötter <hagen.gloetter@gmail.com>"
LABEL description="Video-Konvertierungs-Tool mit H.265/H.264 Hardware-Acceleration"

# Setze non-interactive mode
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Update und installiere Abhängigkeiten
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libx265-dev \
    libx264-dev \
    python3 \
    python3-pip \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Installiere Python-Abhängigkeiten
RUN pip3 install --no-cache-dir \
    pyyaml \
    tqdm

# Erstelle Arbeits-Verzeichnis
WORKDIR /data

# Kopiere Scripts
COPY hg_convert_movie_to_720p_mk3.py /app/
COPY config.yaml /app/
RUN chmod +x /app/hg_convert_movie_to_720p_mk3.py

# Erstelle Ausgabe-Verzeichnisse
RUN mkdir -p /data/{720p,done,logs}

# Default-Kommando
ENTRYPOINT ["/app/hg_convert_movie_to_720p_mk3.py"]
CMD ["--help"]

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ffmpeg -version > /dev/null 2>&1 || exit 1
