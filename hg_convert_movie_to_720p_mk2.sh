#!/bin/bash
# hg_convert_to_720p_h265.sh - Finale Version mit sicherer Dateiverschiebung

# Konfiguration
OUTPUT_DIR="720p"
DONE_DIR="done"
LOG_FILE="conversion_$(date +'%Y-%m-%d_%H-%M-%S').log"
QUALITY=23
MAX_THREADS=$(($(nproc) * 8 / 10))

# Codec-Prüfung
if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "libx265"; then
    CODEC="libx265"
    CODEC_FLAGS="-x265-params crf=$QUALITY"
else
    CODEC="libx264"
    CODEC_FLAGS="-crf $QUALITY"
    echo "Hinweis: H.265 nicht verfügbar, verwende H.264" | tee -a "$LOG_FILE"
fi

# Initialisierung
shopt -s nullglob
echo "=== Konvertierung gestartet $(date +'%Y-%m-%d %H:%M:%S') ===" | tee "$LOG_FILE"
mkdir -p "$OUTPUT_DIR" "$DONE_DIR" || exit 1

# Konvertierungsfunktion mit garantierter Verschiebung
convert_video() {
    local input="$1"
    local basename=$(basename "$input")
    local output="$OUTPUT_DIR/${basename%.*}.mp4"
    
    echo "Verarbeite: $basename" | tee -a "$LOG_FILE"
    local start=$(date +%s)

    # Versionsuche mit H.265/HEVC
    if [ "$CODEC" == "libx265" ]; then
        ffmpeg -hide_banner -i "$input" \
            -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" \
            -c:v libx265 -x265-params crf=$QUALITY \
            -preset slow \
            -c:a aac -b:a 128k \
            -movflags +faststart \
            -tag:v hvc1 \
            "$output" >> "$LOG_FILE" 2>&1
        
        if [ $? -ne 0 ]; then
            echo "H.265 fehlgeschlagen, versuche H.264..." | tee -a "$LOG_FILE"
            rm -f "$output"
        fi
    fi

    # Fallback zu H.264
    if [ ! -f "$output" ]; then
        ffmpeg -hide_banner -i "$input" \
            -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" \
            -c:v libx264 -crf $QUALITY \
            -preset slow \
            -c:a aac -b:a 128k \
            -movflags +faststart \
            "$output" >> "$LOG_FILE" 2>&1
    fi

    # Erfolgsprüfung und Verschiebung
    if [ $? -eq 0 ] && [ -f "$output" ]; then
        if mv -f "$input" "$DONE_DIR/$basename"; then
            echo "Erfolgreich: $basename ($(( $(date +%s) - start ))s)" | tee -a "$LOG_FILE"
            return 0
        else
            echo "WARNUNG: Konvertierung OK, aber Verschieben fehlgeschlagen: $basename" | tee -a "$LOG_FILE"
            return 1
        fi
    else
        echo "FEHLER: Konvertierung fehlgeschlagen: $basename" | tee -a "$LOG_FILE"
        rm -f "$output"
        return 1
    fi
}

# Hauptverarbeitung
count=0
failed=0
for file in *.mp4 *.avi *.mov *.mkv *.webm *.wmv; do
    [ -f "$file" ] || continue
    
    ((count++))
    while [ $(jobs -r | wc -l) -ge "$MAX_THREADS" ]; do sleep 1; done
    
    echo "=== Datei $count: $file ===" | tee -a "$LOG_FILE"
    convert_video "$file" || ((failed++)) &
done

wait

echo "=== Zusammenfassung ===" | tee -a "$LOG_FILE"
echo "Verarbeitet: $count Dateien" | tee -a "$LOG_FILE"
echo "Erfolgreich: $((count - failed)) Dateien" | tee -a "$LOG_FILE"
echo "Fehlgeschlagen: $failed Dateien" | tee -a "$LOG_FILE"
echo "Originale verschoben nach: $DONE_DIR" | tee -a "$LOG_FILE"
echo "Konvertierte Dateien in: $OUTPUT_DIR" | tee -a "$LOG_FILE"