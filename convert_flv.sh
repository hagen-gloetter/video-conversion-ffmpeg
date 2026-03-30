
#!/bin/bash
# hg_convert_flv_to_720p_mp4.sh - FLV zu MP4 Konverter
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
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# System-Erkennung
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

# Encoder-Erkennung
get_encoder() {
    local system=$1
    
    if [[ "$system" == "macOS" ]] && ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "hevc_videotoolbox"; then
        log_info "Nutze hevc_videotoolbox (Apple Silicon/Intel)"
        echo "hevc_videotoolbox"
        return
    fi
    
    if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "hevc_nvenc"; then
        log_info "Nutze hevc_nvenc (NVIDIA GPU)"
        echo "hevc_nvenc"
        return
    fi
    
    if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "libx265"; then
        log_info "Nutze libx265 (H.265/HEVC)"
        echo "libx265"
        return
    fi
    
    if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "libx264"; then
        log_warning "libx265 nicht verfügbar, nutze libx264"
        echo "libx264"
        return
    fi
    
    log_error "Kein passender Video-Encoder gefunden!"
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
                "$output_file" 2>&1 | tee -a "$LOG_FILE"
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
                "$output_file" 2>&1 | tee -a "$LOG_FILE"
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
                "$output_file" 2>&1 | tee -a "$LOG_FILE"
            ;;
        *)
            ffmpeg -hide_banner -loglevel error -i "$input_file" \
                -vf "$(get_scale_filter)" \
                -c:v libx264 \
                -crf "$CRF_VALUE" \
                -preset "$PRESET" \
                -c:a aac -b:a "$AUDIO_BITRATE" \
                -movflags +faststart \
                "$output_file" 2>&1 | tee -a "$LOG_FILE"
            ;;
    esac
    
    if [ $? -eq 0 ] && [ -f "$output_file" ]; then
        if mv "$input_file" "$DONE_DIR/$base_name"; then
            duration=$(($(date +%s) - start_time))
            log_success "Erfolgreich: $base_name (${duration}s) - FLV→MP4"
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

log_info "=== FLV zu MP4 Konvertierung gestartet ==="
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

files=(*.flv)
file_count=${#files[@]}

if [ $file_count -eq 0 ]; then
    log_warning "Keine FLV-Dateien gefunden!"
    exit 0
fi

log_info "Gefunden: $file_count FLV-Dateien"
log_info "========================================"

success=0
failed=0

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        if convert_video "$file" "$ENCODER"; then
            ((success++)) || true
        else
            ((failed++)) || true
        fi
    fi
done

echo "========================================"
log_info "=== ZUSAMMENFASSUNG ==="
log_info "Dateien verarbeitet: $((success + failed))"
log_success "Erfolgreich: $success"
log_error "Fehlgeschlagen: $failed"
log_info "📁 Originale: $DONE_DIR/"
log_info "📁 Konvertiert (MP4): $OUTPUT_DIR/"
log_info "📋 Log-Datei: $LOG_FILE"
echo "========================================"

