#!/bin/bash
# hg_convert_movie_to_720p_parallel.sh - Bash Version mit Parallelisierung
# Optimiert für Ubuntu 22.04/24.04 LTS und M4 Mac
# 08.2020 - Updated 2026

# ============================================================================
# KONFIGURATION - Anpassbar
# ============================================================================
OUTPUT_DIR="720p"
DONE_DIR="done"
LOG_FILE="conversion_$(date +'%Y-%m-%d_%H-%M-%S').log"

# Qualitätseinstellungen
CRF_VALUE=22
PRESET="slow"  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
AUDIO_BITRATE="128k"

# Parallele Verarbeitung
MAX_THREADS=$(($(nproc 2>/dev/null || echo 4) * 8 / 10))  # 80% der CPU-Kerne

# ============================================================================
# FUNKTIONEN
# ============================================================================

# Farben für Terminal-Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2
}

detect_system() {
    local os
    if [[ "$OSTYPE" == "darwin"* ]]; then
        os="macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        os="Linux"
    else
        os="Unknown"
    fi
    log_info "Erkanntes System: $os"
    echo "$os"
}

has_encoder() {
    local encoder="$1"
    ffmpeg -hide_banner -encoders 2>/dev/null | awk -v encoder="$encoder" '$1 ~ /^V/ && $2 == encoder { found=1 } END { exit !found }'
}

encoder_works() {
    local encoder="$1"
    ffmpeg -hide_banner -loglevel error \
        -f lavfi -i testsrc=size=16x16:rate=1 -frames:v 1 \
        -c:v "$encoder" -f null - >/dev/null 2>&1
}

get_encoder() {
    local system=$1
    
    if [[ "$system" == "macOS" ]] && has_encoder "hevc_videotoolbox" && encoder_works "hevc_videotoolbox"; then
        log_info "Nutze hevc_videotoolbox (Apple Silicon/Intel)"
        echo "hevc_videotoolbox"
        return
    elif [[ "$system" == "macOS" ]] && has_encoder "hevc_videotoolbox"; then
        log_warning "hevc_videotoolbox gefunden, aber Test-Encoding fehlgeschlagen"
    fi
    
    if has_encoder "hevc_nvenc" && encoder_works "hevc_nvenc"; then
        log_info "Nutze hevc_nvenc (NVIDIA GPU)"
        echo "hevc_nvenc"
        return
    elif has_encoder "hevc_nvenc"; then
        log_warning "hevc_nvenc gefunden, aber Test-Encoding fehlgeschlagen"
    fi
    
    if has_encoder "libx265" && encoder_works "libx265"; then
        log_info "Nutze libx265 (H.265/HEVC)"
        echo "libx265"
        return
    elif has_encoder "libx265"; then
        log_warning "libx265 gefunden, aber Test-Encoding fehlgeschlagen"
    fi
    
    if has_encoder "libx264" && encoder_works "libx264"; then
        log_warning "libx265 nicht verfügbar, nutze libx264"
        echo "libx264"
        return
    elif has_encoder "libx264"; then
        log_warning "libx264 gefunden, aber Test-Encoding fehlgeschlagen"
    fi

    if has_encoder "mpeg4" && encoder_works "mpeg4"; then
        log_warning "libx265/libx264 nicht verfügbar, nutze mpeg4 als Kompatibilitäts-Fallback"
        echo "mpeg4"
        return
    elif has_encoder "mpeg4"; then
        log_warning "mpeg4 gefunden, aber Test-Encoding fehlgeschlagen"
    fi
    
    log_error "Kein passender Video-Encoder gefunden!"
    log_error "Installiere für bessere Ergebnisse ein FFmpeg-Paket mit libx264/libx265-Unterstützung."
    exit 1
}

get_scale_filter() {
    echo "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2"
}

convert_video() {
    local input_file="$1"
    local encoder="$2"
    local base_name
    local output_file
    local start_time
    local duration
    
    base_name=$(basename "$input_file")
    output_file="$OUTPUT_DIR/${base_name%.*}.mp4"
    start_time=$(date +%s)
    
    log_info "Starte Konvertierung: $base_name (Encoder: $encoder)"
    
    case "$encoder" in
        hevc_videotoolbox)
            ffmpeg -hide_banner -loglevel error -i "$input_file" \
                -vf "$(get_scale_filter)" \
                -c:v hevc_videotoolbox \
                -q:v 75 \
                -c:a aac -b:a "$AUDIO_BITRATE" \
                -movflags +faststart \
                -tag:v hvc1 \
                "$output_file" 2>&1
            ;;
        hevc_nvenc)
            ffmpeg -hide_banner -loglevel error -i "$input_file" \
                -vf "$(get_scale_filter)" \
                -c:v hevc_nvenc \
                -preset slow \
                -rc vbr \
                -cq 22 \
                -c:a aac -b:a "$AUDIO_BITRATE" \
                -movflags +faststart \
                -tag:v hvc1 \
                "$output_file" 2>&1
            ;;
        libx265)
            ffmpeg -hide_banner -loglevel error -i "$input_file" \
                -vf "$(get_scale_filter)" \
                -c:v libx265 \
                -x265-params "crf=$CRF_VALUE:aq-mode=3:qg-size=8:aq-strength=1.2" \
                -preset "$PRESET" \
                -c:a aac -b:a "$AUDIO_BITRATE" \
                -movflags +faststart \
                -tag:v hvc1 \
                "$output_file" 2>&1
            ;;
        libx264)
            ffmpeg -hide_banner -loglevel error -i "$input_file" \
                -vf "$(get_scale_filter)" \
                -c:v libx264 \
                -crf "$CRF_VALUE" \
                -preset "$PRESET" \
                -c:a aac -b:a "$AUDIO_BITRATE" \
                -movflags +faststart \
                "$output_file" 2>&1
            ;;
        mpeg4)
            ffmpeg -hide_banner -loglevel error -i "$input_file" \
                -vf "$(get_scale_filter)" \
                -c:v mpeg4 \
                -q:v 5 \
                -c:a aac -b:a "$AUDIO_BITRATE" \
                -movflags +faststart \
                "$output_file" 2>&1
            ;;
    esac
    
    if [ $? -eq 0 ] && [ -f "$output_file" ]; then
        if mv "$input_file" "$DONE_DIR/$base_name"; then
            duration=$(($(date +%s) - start_time))
            log_success "Erfolgreich: $base_name (${duration}s)"
            return 0
        else
            log_error "Verschieben fehlgeschlagen: $base_name"
            return 1
        fi
    else
        log_error "Konvertierung fehlgeschlagen: $base_name"
        [ -f "$output_file" ] && rm -f "$output_file"
        return 1
    fi
}

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

set -euo pipefail

# In Zielverzeichnis wechseln falls als Parameter übergeben
TARGET_DIR="${1:-.}"
if [ ! -d "$TARGET_DIR" ]; then
    log_error "Verzeichnis nicht gefunden: $TARGET_DIR"
    exit 1
fi
cd "$TARGET_DIR"

log_info "=== Video-Konvertierung gestartet (Parallel) ==="
log_info "Arbeitsverzeichnis: $(pwd)"
log_info "CPU-Kerne: $(nproc 2>/dev/null || echo ?) | Max Threads: $MAX_THREADS"
log_info "Qualität: CRF=$CRF_VALUE | Preset=$PRESET | Audio=$AUDIO_BITRATE"

if ! command -v ffmpeg &> /dev/null; then
    log_error "FFmpeg nicht gefunden!"
    log_error "Ubuntu: sudo apt-get install ffmpeg"
    log_error "macOS: brew install ffmpeg"
    exit 1
fi

log_info "✓ FFmpeg gefunden"

mkdir -p "$OUTPUT_DIR" "$DONE_DIR"
shopt -s nullglob

SYSTEM=$(detect_system)
ENCODER=$(get_encoder "$SYSTEM")

files=(*.mp4 *.avi *.mov *.mkv *.webm *.wmv)
file_count=${#files[@]}

if [ $file_count -eq 0 ]; then
    log_warning "Keine passenden Videodateien gefunden!"
    exit 0
fi

log_info "Gefunden: $file_count Dateien"
log_info "========================================"

success=0
failed=0
count=0
completed=0
pids=()

wait_for_next_job() {
    local pid="${pids[0]}"

    if wait "$pid"; then
        success=$((success + 1))
    else
        failed=$((failed + 1))
    fi

    completed=$((completed + 1))
    pids=("${pids[@]:1}")
    log_info "Fortschritt: $completed/$file_count abgeschlossen (Erfolgreich: $success | Fehlgeschlagen: $failed)"
}

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        count=$((count + 1))
        
        # Warte auf freien Slot wenn max Threads erreicht
        while [ "${#pids[@]}" -ge "$MAX_THREADS" ]; do
            wait_for_next_job
        done
        
        # Starte Konvertierung im Hintergrund
        log_info "Plane Datei $count/$file_count: $file"
        convert_video "$file" "$ENCODER" >> "$LOG_FILE" 2>&1 &
        pids+=("$!")
    fi
done

# Warte auf alle Background-Jobs
while [ "${#pids[@]}" -gt 0 ]; do
    wait_for_next_job
done

echo "========================================"
log_info "=== ZUSAMMENFASSUNG ==="
log_info "Dateien verarbeitet: $((success + failed))"
log_success "Erfolgreich: $success"
log_error "Fehlgeschlagen: $failed"
log_info "📁 Originale: $DONE_DIR/"
log_info "📁 Konvertiert: $OUTPUT_DIR/"
log_info "📋 Log-Datei: $LOG_FILE"
echo "========================================"
