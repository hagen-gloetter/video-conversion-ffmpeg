#!/usr/bin/env python3
# hg_convert_to_720p_h265.py - Python Version
# Optimiert für Ubuntu 22.04/24.04 LTS und M4 Mac mit Hardware-Acceleration
# STANDALONE - Alle Parameter im Code, einfach kopieren und nutzen!

import os
import subprocess
import concurrent.futures
from datetime import datetime
import logging
import shutil
import platform

# ============================================================================
# KONFIGURATION - Alles anpassbar, kein externe config nötig!
# ============================================================================
OUTPUT_DIR = "720p"                     # Ziel-Verzeichnis
DONE_DIR = "done"                       # Quelle nach erfolgreicher Konvertierung hierhin
LOG_DIR = "logs"                        # Protokoll-Verzeichnis
LOG_FILE = f"conversion_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

# Qualitätseinstellungen
# CRF: 0-51 (0=lossless, 23=default, 51=worst)
# Kleinere CRF = bessere Qualität aber größere Dateigröße
CRF_VALUE = 22                          # 23=default, 22=besser, 20=sehr gut, 18=maximum

# Preset: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
# Slower = bessere Kompression aber längere Verarbeitung
PRESET = "slow"                         # slow=besser, medium=balance, fast=schnell

# Audio-Bitrate (128k, 192k, 256k, etc.)
AUDIO_BITRATE = "128k"                  # 128k, 192k, 256k, etc.

# Skalierung & Padding
SCALE_FILTER = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2"

# Maximale Threads (% der CPU-Kerne)
MAX_THREADS = max(1, int((os.cpu_count() or 4) * 0.8))  # 80% der CPU-Kerne

# Unterstützte Formate
SUPPORTED_FORMATS = ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv', '.flv', 'm4v')

# Fehlerbehandlung
MAX_RETRIES = 3                         # Neuversuche bei Fehler
RETRY_WAIT_SECONDS = 5                  # Warten zwischen Versuchen
CONVERSION_TIMEOUT_SECONDS = 3600       # 1 Stunde Timeout pro Video

# Bereinigung
MOVE_ORIGINAL = True                    # Quelle nach DONE_DIR verschieben
REMOVE_INCOMPLETE = True                # Unvollständige Dateien löschen


# ============================================================================
# SYSTEM-ERKENNUNG
# ============================================================================
SYSTEM = platform.system()
IS_MAC = SYSTEM == "Darwin"
IS_LINUX = SYSTEM == "Linux"

# Logging einrichten
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

# ============================================================================
# CODEC-ERKENNUNG & OPTIMIERUNG
# ============================================================================
def get_available_encoder():
    """
    Findet optimalen Video-Encoder für das System:
    1. hevc_videotoolbox (Apple Silicon/Intel Mac)
    2. hevc_nvenc (NVIDIA GPU)
    3. libx265 (Software-Encoder, beste Qualität)
    4. libx264 (Fallback, große Kompatibilität)
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        encoders = result.stdout
        
        # Hardware-Encoder (Apple Mac)
        if IS_MAC and "hevc_videotoolbox" in encoders:
            logging.info("Nutze hevc_videotoolbox (Apple Silicon)")
            return "hevc_videotoolbox"
        
        # Hardware-Encoder (NVIDIA)
        if "hevc_nvenc" in encoders:
            logging.info("Nutze hevc_nvenc (NVIDIA GPU)")
            return "hevc_nvenc"
        
        # Software-Encoder H.265
        if "libx265" in encoders:
            logging.info("Nutze libx265 (H.265/HEVC)")
            return "libx265"
        
        # Fallback H.264
        if "libx264" in encoders:
            logging.warning("libx265 nicht verfügbar, nutze libx264")
            return "libx264"
        
        raise Exception("Kein passender Video-Encoder gefunden!")
        
    except Exception as e:
        logging.error(f"Encoder-Erkennung fehlgeschlagen: {e}")
        raise

def check_ffmpeg():
    """Prüft FFmpeg-Installation und Codec-Verfügbarkeit"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        if result.returncode != 0:
            raise Exception("FFmpeg antwortet mit Fehler")
        logging.info(f"✓ FFmpeg verfügbar")
        return True
    except FileNotFoundError:
        logging.error("FFmpeg nicht gefunden! Installation erforderlich.")
        logging.error("Ubuntu: sudo apt-get install ffmpeg")
        logging.error("macOS: brew install ffmpeg")
        raise
    except Exception as e:
        logging.error(f"FFmpeg-Fehler: {e}")
        raise

def get_h265_params(encoder):
    """
    Optimierte H.265 Parameter basierend auf Encoder
    
    aq-mode=3: Bessere Adaptive Quantization (Qualität)
    qg-size=8: Größere Quantization Groups (bessere Kompression)
    aq-strength=1.2: Stärke der Quality-Adaption
    """
    if encoder == "libx265":
        return f"crf={CRF_VALUE}:aq-mode=3:qg-size=8:aq-strength=1.2"
    return f"crf={CRF_VALUE}"

def build_ffmpeg_command(input_file, output_file, encoder):
    """
    Erstellt optimiertes FFmpeg-Kommando mit Skalierung und Audio
    
    Video-Filter: 
    - scale: Skaliert auf 1280x720 mit Aspect-Ratio-Erhaltung
    - pad: Zentriert das Bild mit Padding bei unterschiedlichen Aspekten
    """
    
    base_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-i", input_file,
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        output_file
    ]
    
    if encoder == "hevc_videotoolbox":
        # Apple Hardware-Encoder (sehr schnell, anständige Qualität)
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", input_file,
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "hevc_videotoolbox",
            "-q:v", "75",  # Qualität 0-100
            "-c:a", "aac", "-b:a", AUDIO_BITRATE,
            "-movflags", "+faststart",
            "-tag:v", "hvc1",
            output_file
        ]
    elif encoder == "hevc_nvenc":
        # NVIDIA Hardware-Encoder
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", input_file,
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "hevc_nvenc",
            "-preset", "slow",  # fast, medium, slow
            "-rc", "vbr",  # Variable Bitrate für bessere Qualität
            "-cq", "22",  # Quality Level
            "-c:a", "aac", "-b:a", AUDIO_BITRATE,
            "-movflags", "+faststart",
            "-tag:v", "hvc1",
            output_file
        ]
    elif encoder == "libx265":
        # Software H.265 Encoder (beste Kompression)
        h265_params = get_h265_params(encoder)
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", input_file,
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx265",
            "-x265-params", h265_params,
            "-preset", PRESET,
            "-c:a", "aac", "-b:a", AUDIO_BITRATE,
            "-movflags", "+faststart",
            "-tag:v", "hvc1",
            output_file
        ]
    else:
        # Fallback H.264
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", input_file,
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-crf", str(CRF_VALUE),
            "-preset", PRESET,
            "-c:a", "aac", "-b:a", AUDIO_BITRATE,
            "-movflags", "+faststart",
            output_file
        ]
    
    return cmd

def convert_video(input_file, encoder):
    """Konvertiert eine einzelne Datei mit intelligentem Fallback"""
    base_name = os.path.basename(input_file)
    output_file = os.path.join(
        OUTPUT_DIR,
        f"{os.path.splitext(base_name)[0]}.mp4"
    )
    
    logging.info(f"Starte Konvertierung: {base_name} (Encoder: {encoder})")
    start_time = datetime.now()

    cmd = build_ffmpeg_command(input_file, output_file, encoder)
    
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=3600  # 1 Stunde Timeout
        )
    except subprocess.CalledProcessError as e:
        logging.warning(f"Konvertierung mit {encoder} fehlgeschlagen: {base_name}")
        
        # Fallback-Chain: Versuche nächsten Encoder
        fallback_encoders = {
            "hevc_videotoolbox": "libx265",
            "hevc_nvenc": "libx265",
            "libx265": "libx264",
            "libx264": None
        }
        
        fallback = fallback_encoders.get(encoder)
        if fallback:
            logging.info(f"Versuche Fallback-Encoder: {fallback}")
            return convert_video(input_file, fallback)
        else:
            logging.error(f"Alle Encoder ausgeschöpft, Datei kann nicht konvertiert werden: {base_name}")
            if os.path.exists(output_file):
                os.remove(output_file)
            return False
    except subprocess.TimeoutExpired:
        logging.error(f"Konvertierung abgebrochen (Timeout): {base_name}")
        if os.path.exists(output_file):
            os.remove(output_file)
        return False

    # Erfolgreich - verschiebe Original
    try:
        shutil.move(input_file, os.path.join(DONE_DIR, base_name))
        duration = (datetime.now() - start_time).total_seconds()
        file_size_original = os.path.getsize(os.path.join(DONE_DIR, base_name)) / 1024 / 1024
        file_size_new = os.path.getsize(output_file) / 1024 / 1024
        compression = (1 - file_size_new / file_size_original) * 100 if file_size_original > 0 else 0
        logging.info(
            f"✓ Erfolgreich: {base_name} ({duration:.1f}s) "
            f"[{file_size_original:.1f}MB → {file_size_new:.1f}MB ({compression:.1f}% Ersparnis)]"
        )
        return True
    except OSError as e:
        logging.error(f"Verschieben fehlgeschlagen: {base_name} - {str(e)}")
        return False

def main():
    """Hauptfunktion"""
    logging.info(f"=== Video-Konvertierung gestartet ===")
    logging.info(f"Plattform: {SYSTEM}")
    logging.info(f"CPU-Threads: {os.cpu_count()} (nutze {MAX_THREADS})")
    logging.info(f"Video-Preset: {PRESET} | CRF: {CRF_VALUE} | Audio: {AUDIO_BITRATE}")
    
    # FFmpeg-Prüfung
    try:
        check_ffmpeg()
    except Exception as e:
        logging.error("Abbruch: FFmpeg nicht verfügbar")
        return
    
    # Verzeichnisse erstellen
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(DONE_DIR, exist_ok=True)
    except OSError as e:
        logging.error(f"Verzeichnis-Fehler: {e}")
        return

    # Verfügbare Dateien finden
    files = [
        f for f in os.listdir('.') 
        if os.path.isfile(f) and f.lower().endswith(SUPPORTED_FORMATS)
    ]

    if not files:
        logging.warning("Keine passenden Videodateien gefunden!")
        logging.warning(f"Unterstützte Formate: {', '.join(SUPPORTED_FORMATS)}")
        return

    logging.info(f"Gefunden: {len(files)} Dateien zur Konvertierung")
    
    # Encoder auswählen
    try:
        encoder = get_available_encoder()
    except Exception as e:
        logging.error(f"Kann keinen Encoder auswählen: {e}")
        return

    # Parallele Verarbeitung mit Wrapper
    def convert_with_encoder(input_file):
        return convert_video(input_file, encoder)
    
    success = 0
    failed = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for result in concurrent.futures.as_completed(
            [executor.submit(convert_with_encoder, f) for f in files]
        ):
            try:
                if result.result():
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logging.error(f"Unerwarteter Fehler: {e}")
                failed += 1

    # Zusammenfassung
    total_processed = success + failed
    success_rate = (success / total_processed * 100) if total_processed > 0 else 0
    
    logging.info("=" * 70)
    logging.info("=== ZUSAMMENFASSUNG ===")
    logging.info(f"Dateien verarbeitet: {total_processed}")
    logging.info(f"✓ Erfolgreich: {success} ({success_rate:.1f}%)")
    logging.info(f"✗ Fehlgeschlagen: {failed}")
    logging.info(f"📁 Originale: {DONE_DIR}/")
    logging.info(f"📁 Konvertiert: {OUTPUT_DIR}/")
    logging.info("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Konvertierung vom Benutzer unterbrochen")
    except Exception as e:
        logging.error(f"Kritischer Fehler: {str(e)}", exc_info=True)