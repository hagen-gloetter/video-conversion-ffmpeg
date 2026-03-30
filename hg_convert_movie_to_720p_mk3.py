#!/usr/bin/env python3
"""
Video-Konvertierungs-Tool mit Hardware-Acceleration
Funktioniert standalone - alle Parameter im Code definiert
Optional: config.yaml zum Überschreiben von Einstellungen
"""

import os
import sys
import json
import subprocess
import concurrent.futures
from datetime import datetime, timedelta
import logging
import shutil
import platform
import argparse
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ============================================================================
# EXTERNE ABHÄNGIGKEITEN (optional)
# ============================================================================
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ============================================================================
# INLINE-KONFIGURATION (Standalone - einfach anpassen!)
# ============================================================================
# Verzeichnisse
OUTPUT_DIR = "720p"
DONE_DIR = "done"
LOG_DIR = "logs"

# Kodierungsparameter
CRF_VALUE = 22                          # 23=default, 22=besser, 20=sehr gut, 18=max
PRESET = "slow"                         # ultrafast|superfast|veryfast|faster|fast|medium|slow|slower|veryslow
AUDIO_BITRATE = "128k"                  # 128k, 192k, 256k, etc.
SCALE_FILTER = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2"

# Presets (schnell, balanced, high_quality, ultra)
PRESETS = {
    'fast': {'crf': 24, 'preset': 'fast', 'audio_bitrate': '128k'},
    'balanced': {'crf': 22, 'preset': 'medium', 'audio_bitrate': '128k'},
    'high_quality': {'crf': 20, 'preset': 'slow', 'audio_bitrate': '192k'},
    'ultra': {'crf': 18, 'preset': 'veryslow', 'audio_bitrate': '256k'}
}

# Filter & Formate
SUPPORTED_FORMATS = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv', 'flv', 'm4v', 'mts', 'm2ts']
MIN_FILE_SIZE_MB = 0                    # 0 = keine Begrenzung
MIN_RESOLUTION_HEIGHT = 0               # 0 = keine Begrenzung
EXCLUDE_FORMATS = []                    # z.B. ['flv', 'wmv']

# Parallel-Verarbeitung
MAX_THREADS = max(1, int((os.cpu_count() or 4) * 0.8))  # 80% der CPU-Kerne

# Fehlerbehandlung
MAX_RETRIES = 3                         # Neuversuche bei Fehler
RETRY_WAIT_SECONDS = 5                  # Warten zwischen Versuchen
CONVERSION_TIMEOUT_SECONDS = 3600       # 1 Stunde Timeout

# Cleaner
MOVE_ORIGINAL = True                    # Quelle nach done/ verschieben
REMOVE_INCOMPLETE = True                # Incomplete Dateien löschen
CREATE_BACKUP = False                   # Backup der Originale erstellen

# Logging & Reports
SAVE_LOGS = True
REPORT_FORMAT = 'txt'                   # 'txt' oder 'json'
SHOW_PROGRESS = True
SHOW_VIDEO_INFO = True

# ============================================================================
# FALLBACK-KONFIGURATION (aus den Inline-Parametern generiert)
# ============================================================================
def get_default_config() -> Dict:
    """Erstellt Config-Dict aus Inline-Parametern"""
    return {
        'encoding': {
            'crf_value': CRF_VALUE,
            'preset': PRESET,
            'audio_bitrate': AUDIO_BITRATE,
            'scale_filter': SCALE_FILTER
        },
        'presets': PRESETS,
        'directories': {'output': OUTPUT_DIR, 'done': DONE_DIR, 'logs': LOG_DIR},
        'parallel': {'cpu_usage': 0.8, 'max_threads': MAX_THREADS},
        'formats': {'supported': SUPPORTED_FORMATS},
        'filters': {'min_file_size_mb': MIN_FILE_SIZE_MB, 'min_resolution_height': MIN_RESOLUTION_HEIGHT, 'exclude_formats': EXCLUDE_FORMATS},
        'cleanup': {'move_original': MOVE_ORIGINAL, 'remove_incomplete': REMOVE_INCOMPLETE, 'create_backup': CREATE_BACKUP},
        'logging': {'level': 'INFO', 'save_logs': SAVE_LOGS, 'create_report': True, 'report_format': REPORT_FORMAT},
        'error_handling': {'max_retries': MAX_RETRIES, 'retry_wait_seconds': RETRY_WAIT_SECONDS, 'stop_on_error': False},
        'performance': {'show_progress': SHOW_PROGRESS, 'conversion_timeout_seconds': CONVERSION_TIMEOUT_SECONDS, 'show_video_info': SHOW_VIDEO_INFO}
    }

DEFAULT_CONFIG = get_default_config()

# ============================================================================
# GLOBALE VARIABLEN
# ============================================================================
SYSTEM = platform.system()
IS_MAC = SYSTEM == "Darwin"
IS_LINUX = SYSTEM == "Linux"
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / 'config.yaml'
RESUME_FILE = SCRIPT_DIR / '.conversion.resume'
STATS_FILE = None


# ============================================================================
# LOGGING SETUP
# ============================================================================
def setup_logging(log_level='INFO', save_logs=True, log_dir='logs'):
    """Konfiguriert Logging mit File & Console Output"""
    log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Verzeichnis
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Console Handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(console)
    
    # File Handler
    if save_logs:
        log_file = log_path / f"conversion_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(file_handler)
        return logger, log_file
    
    return logger, None

# ============================================================================
# KONFIGURATION LADEN
# ============================================================================
def load_config(config_file: Optional[str] = None) -> Dict:
    """
    Lädt Konfiguration mit Inline-Parametern als Basis
    Optional: config.yaml wird geladen und merged wenn vorhanden
    """
    config = DEFAULT_CONFIG.copy()
    
    # Versuche config.yaml zu laden (optional)
    config_path = Path(config_file) if config_file else CONFIG_FILE
    
    if HAS_YAML and config_path.exists():
        try:
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
            if user_config:
                # Merge mit Inline-Defaults
                for key in user_config:
                    if isinstance(user_config[key], dict) and key in config:
                        config[key].update(user_config[key])
                    else:
                        config[key] = user_config[key]
                logging.info(f"✓ config.yaml geladen: {config_path}")
                return config
        except Exception as e:
            logging.warning(f"config.yaml Fehler: {e}, nutze Inline-Parameter")
    elif config_file and not config_path.exists():
        logging.warning(f"config.yaml nicht gefunden: {config_path}, nutze Inline-Parameter")
    else:
        logging.info(f"✓ Inline-Parameter geladen (config.yaml optional)")
    
    return config

# ============================================================================
# ENCODER-ERKENNUNG
# ============================================================================
def check_ffmpeg():
    """Prüft FFmpeg-Installation"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5, check=True)
        logging.info("✓ FFmpeg verfügbar")
        return True
    except Exception as e:
        logging.error(f"FFmpeg nicht verfügbar: {e}")
        logging.error("Ubuntu: sudo apt-get install ffmpeg")
        logging.error("macOS: brew install ffmpeg")
        return False

def check_ffprobe():
    """Prüft ffprobe Verfügbarkeit"""
    try:
        subprocess.run(['ffprobe', '-version'], capture_output=True, timeout=5, check=True)
        return True
    except:
        return False

def get_available_encoder() -> str:
    """Findet optimalen Video-Encoder"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            capture_output=True, text=True, timeout=5
        )
        encoders = result.stdout
        
        if IS_MAC and 'hevc_videotoolbox' in encoders:
            logging.info("🍎 Hardware-Encoder: hevc_videotoolbox (Apple Silicon)")
            return "hevc_videotoolbox"
        
        if 'hevc_nvenc' in encoders:
            logging.info("🔷 Hardware-Encoder: hevc_nvenc (NVIDIA GPU)")
            return "hevc_nvenc"
        
        if 'libx265' in encoders:
            logging.info("💻 Software-Encoder: libx265 (H.265/HEVC)")
            return "libx265"
        
        if 'libx264' in encoders:
            logging.info("⚙️ Fallback-Encoder: libx264 (H.264)")
            return "libx264"
        
        raise Exception("Kein Video-Encoder verfügbar")
    except Exception as e:
        logging.error(f"Encoder-Erkennung fehlgeschlagen: {e}")
        raise

# ============================================================================
# VIDEO-INFORMATION MIT FFPROBE
# ============================================================================
def get_video_info(input_file: str) -> Optional[Dict]:
    """Holt Video-Informationen (Auflösung, Dauer, Codec)"""
    if not check_ffprobe():
        return None
    
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,codec_name,duration',
            '-of', 'json',
            input_file
        ], capture_output=True, text=True, timeout=10)
        
        data = json.loads(result.stdout)
        if data.get('streams'):
            stream = data['streams'][0]
            return {
                'width': stream.get('width'),
                'height': stream.get('height'),
                'codec': stream.get('codec_name'),
                'duration': float(stream.get('duration', 0))
            }
    except:
        pass
    
    return None

# ============================================================================
# DATEI-FILTERING
# ============================================================================
def should_convert_file(file_path: str, config: Dict) -> Tuple[bool, str]:
    """Prüft ob Datei konvertiert werden soll"""
    filters = config.get('filters', {})
    
    # Format-Check
    ext = Path(file_path).suffix.lower().lstrip('.')
    exclude = filters.get('exclude_formats', [])
    if ext in [e.lstrip('.').lower() for e in exclude]:
        return False, f"Format ausgeschlossen: {ext}"
    
    # Größen-Check
    min_size = filters.get('min_file_size_mb', 0)
    if min_size > 0:
        file_size = Path(file_path).stat().st_size / 1024 / 1024
        if file_size < min_size:
            return False, f"Dateigröße zu klein: {file_size:.1f}MB < {min_size}MB"
    
    # Auflösungs-Check
    min_res = filters.get('min_resolution_height', 0)
    if min_res > 0 and config['performance'].get('show_video_info'):
        info = get_video_info(file_path)
        if info and info['height'] and info['height'] < min_res:
            return False, f"Auflösung zu klein: {info['height']}p < {min_res}p"
    
    return True, ""

# ============================================================================
# KONVERTIERUNG
# ============================================================================
def build_ffmpeg_command(input_file: str, output_file: str, encoder: str, config: Dict) -> List[str]:
    """Erstellt optimiertes FFmpeg-Kommando"""
    enc = config['encoding']
    scale = enc.get('scale_filter', DEFAULT_CONFIG['encoding']['scale_filter'])
    
    base_cmd = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error',
        '-i', input_file,
        '-vf', scale,
        '-c:a', 'aac', '-b:a', enc.get('audio_bitrate', '128k'),
        '-movflags', '+faststart',
        output_file
    ]
    
    if encoder == 'hevc_videotoolbox':
        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', input_file,
            '-vf', scale,
            '-c:v', 'hevc_videotoolbox', '-q:v', '75',
            '-c:a', 'aac', '-b:a', enc.get('audio_bitrate', '128k'),
            '-movflags', '+faststart', '-tag:v', 'hvc1',
            output_file
        ]
    elif encoder == 'hevc_nvenc':
        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', input_file,
            '-vf', scale,
            '-c:v', 'hevc_nvenc', '-preset', enc.get('preset', 'slow'), '-rc', 'vbr',
            '-cq', str(enc.get('crf_value', 22)),
            '-c:a', 'aac', '-b:a', enc.get('audio_bitrate', '128k'),
            '-movflags', '+faststart', '-tag:v', 'hvc1',
            output_file
        ]
    elif encoder == 'libx265':
        x265_params = f"crf={enc.get('crf_value', 22)}:aq-mode=3:qg-size=8:aq-strength=1.2"
        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', input_file,
            '-vf', scale,
            '-c:v', 'libx265', '-x265-params', x265_params,
            '-preset', enc.get('preset', 'slow'),
            '-c:a', 'aac', '-b:a', enc.get('audio_bitrate', '128k'),
            '-movflags', '+faststart', '-tag:v', 'hvc1',
            output_file
        ]
    else:  # libx264 fallback
        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', input_file,
            '-vf', scale,
            '-c:v', 'libx264', '-crf', str(enc.get('crf_value', 22)),
            '-preset', enc.get('preset', 'slow'),
            '-c:a', 'aac', '-b:a', enc.get('audio_bitrate', '128k'),
            '-movflags', '+faststart',
            output_file
        ]
    
    return cmd

def convert_video(input_file: str, output_file: str, encoder: str, config: Dict, 
                   max_retries: int = 3, dry_run: bool = False) -> bool:
    """Konvertiert einzelne Datei mit Retry-Logik"""
    base_name = Path(input_file).name
    timeout = config['performance'].get('conversion_timeout_seconds', 3600)
    
    # Video-Info anzeigen
    if config['performance'].get('show_video_info'):
        info = get_video_info(input_file)
        if info:
            logging.info(f"  📺 {info['width']}×{info['height']} {info['codec']} "
                        f"({timedelta(seconds=int(info['duration']))})")
    
    if dry_run:
        file_size = Path(input_file).stat().st_size / 1024 / 1024
        logging.info(f"  [DRY-RUN] Würde konvertieren: {base_name} ({file_size:.1f}MB)")
        return True
    
    cmd = build_ffmpeg_command(input_file, output_file, encoder, config)
    start_time = time.time()
    
    for attempt in range(max_retries):
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
            
            if not Path(output_file).exists():
                raise Exception("Output-Datei nicht erstellt")
            
            # Dateigröße berechnen
            orig_size = Path(input_file).stat().st_size / 1024 / 1024
            new_size = Path(output_file).stat().st_size / 1024 / 1024
            compression = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0
            duration = time.time() - start_time
            
            logging.info(f"  ✓ {orig_size:.1f}MB → {new_size:.1f}MB ({compression:.1f}% Ersparnis, {duration:.0f}s)")
            
            # Verschiebe Original
            if config['cleanup'].get('move_original'):
                done_file = Path(config['directories']['done']) / base_name
                shutil.move(input_file, done_file)
            
            return True
            
        except subprocess.TimeoutExpired:
            logging.error(f"  ⏱️ Timeout (Versuch {attempt+1}/{max_retries})")
            Path(output_file).unlink(missing_ok=True)
        except Exception as e:
            logging.error(f"  ❌ Fehler: {e} (Versuch {attempt+1}/{max_retries})")
            Path(output_file).unlink(missing_ok=True)
        
        if attempt < max_retries - 1:
            wait_time = config['error_handling'].get('retry_wait_seconds', 5)
            logging.info(f"  ⏳ Warte {wait_time}s bevor neu versucht...")
            time.sleep(wait_time)
    
    return False

# ============================================================================
# RESUME-FUNKTIONALITÄT
# ============================================================================
def save_resume_state(processed_files: set):
    """Speichert welche Dateien bereits verarbeitet wurden"""
    with open(RESUME_FILE, 'w') as f:
        json.dump(list(processed_files), f)

def load_resume_state() -> set:
    """Lädt vorher verarbeitete Dateien"""
    if RESUME_FILE.exists():
        try:
            with open(RESUME_FILE) as f:
                return set(json.load(f))
        except:
            pass
    return set()

# ============================================================================
# STATISTIK & REPORTING
# ============================================================================
def create_report(stats: Dict, config: Dict, log_file: Optional[Path]):
    """Erstellt Statistik-Report"""
    report_format = config['logging'].get('report_format', 'txt')
    report_file = Path(config['directories']['logs']) / \
                  f"report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.{report_format}"
    
    total = stats['success'] + stats['failed']
    success_rate = (stats['success'] / total * 100) if total > 0 else 0
    total_time = timedelta(seconds=int(stats['total_time']))
    
    if report_format == 'txt':
        content = f"""
KONVERTIERUNGS-STATISTIK
={'='*70}
Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Gesamtdauer: {total_time}
Plattform: {SYSTEM}
Encoder: {stats.get('encoder', 'Unbekannt')}

ERGEBNISSE
{'='*70}
Dateien gesamt: {total}
✓ Erfolgreich: {stats['success']} ({success_rate:.1f}%)
✗ Fehlgeschlagen: {stats['failed']}

SPEICHERPLATZ
{'='*70}
Original: {stats['original_size_total']:.1f}MB
Konvertiert: {stats['converted_size_total']:.1f}MB
Ersparnis: {stats['compression_percent']:.1f}%

DURCHSCHNITTSWERTE
{'='*70}
Zeit pro Datei: {(stats['total_time'] / total):.0f} Sekunden
Größe Original: {(stats['original_size_total'] / total):.1f}MB
Größe Konvertiert: {(stats['converted_size_total'] / total):.1f}MB

VERZEICHNISSE
{'='*70}
Originale: {Path(config['directories']['done']).absolute()}
Konvertiert: {Path(config['directories']['output']).absolute()}
Logs: {Path(config['directories']['logs']).absolute()}
        """.strip()
    else:  # json
        content = json.dumps({
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': int(stats['total_time']),
            'platform': SYSTEM,
            'encoder': stats.get('encoder'),
            'total_files': total,
            'successful': stats['success'],
            'failed': stats['failed'],
            'success_rate_percent': success_rate,
            'original_size_mb': stats['original_size_total'],
            'converted_size_mb': stats['converted_size_total'],
            'compression_percent': stats['compression_percent']
        }, indent=2)
    
    report_file.write_text(content)
    logging.info(f"📊 Report erstellt: {report_file}")

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description='Professionelle Video-Konvertierung')
    parser.add_argument('--preset', choices=['fast', 'balanced', 'high_quality', 'ultra'],
                       help='Qualitäts-Preset')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Zeige was konvertiert würde, führe nicht aus')
    parser.add_argument('--min-size', type=float, metavar='MB',
                       help='Minimale Dateigröße')
    parser.add_argument('--min-res', type=int, metavar='PX',
                       help='Minimale Videoauflösung (Höhe)')
    parser.add_argument('--exclude', nargs='+', metavar='FORMAT',
                       help='Formate ausschließen (z.B. mov flv)')
    parser.add_argument('--resume', action='store_true',
                       help='Fahre mit unterbrochener Konvertierung fort')
    parser.add_argument('--config', type=str, help='Pfad zu config.yaml')
    
    args = parser.parse_args()
    
    # Config laden (mit optionalem config-Datei-Pfad)
    config = load_config(args.config)

    # Logging setup
    logger, log_file = setup_logging(
        log_level=config['logging'].get('level', 'INFO'),
        save_logs=config['logging'].get('save_logs', True),
        log_dir=config['directories'].get('logs', 'logs')
    )
    
    # FFmpeg prüfen
    if not check_ffmpeg():
        return 1
    
    # Wende CLI-Argumente an
    if args.preset:
        preset_config = config['presets'].get(args.preset)
        if preset_config:
            config['encoding'].update(preset_config)
            logging.info(f"📋 Preset verwendet: {args.preset}")
    
    if args.min_size:
        config['filters']['min_file_size_mb'] = args.min_size
    
    if args.min_res:
        config['filters']['min_resolution_height'] = args.min_res
    
    if args.exclude:
        config['filters']['exclude_formats'] = args.exclude
    
    # Verzeichnisse erstellen
    for dir_key in ['output', 'done', 'logs']:
        Path(config['directories'][dir_key]).mkdir(exist_ok=True)
    
    # Dateien finden
    supported_ext = tuple(f".{ext.lower()}" for ext in config['formats']['supported'])
    files = [
        str(f) for f in Path('.').glob('*')
        if f.is_file() and f.suffix.lower() in supported_ext
    ]
    
    # Resume laden
    processed = load_resume_state() if args.resume else set()
    files = [f for f in files if f not in processed]
    
    if not files:
        logging.warning("Keine passenden Dateien gefunden")
        return 0
    
    logging.info(f"Gefunden: {len(files)} Dateien")
    
    # Encoder
    try:
        encoder = get_available_encoder()
    except Exception as e:
        logging.error(f"Encoder-Erkennung fehlgeschlagen: {e}")
        return 1
    
    # Konvertierung
    stats = {
        'success': 0, 'failed': 0, 'total_time': 0,
        'original_size_total': 0, 'converted_size_total': 0,
        'compression_percent': 0, 'encoder': encoder
    }
    
    start_total = time.time()
    
    # Progress Bar
    file_iterator = tqdm(files, desc="Konvertierung") if HAS_TQDM else files
    
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=config['parallel'].get('max_threads') or 
                   max(1, int((os.cpu_count() or 4) * config['parallel'].get('cpu_usage', 0.8)))
    ) as executor:
        futures = {}
        
        for file in files:
            # Filter prüfen
            should_convert, reason = should_convert_file(file, config)
            if not should_convert:
                logging.info(f"⊘ Übersprungen: {file} ({reason})")
                continue
            
            output_file = str(Path(config['directories']['output']) / 
                            f"{Path(file).stem}.mp4")
            
            future = executor.submit(
                convert_video, file, output_file, encoder, config,
                config['error_handling'].get('max_retries', 3),
                args.dry_run
            )
            futures[future] = (file, output_file)
        
        for future in concurrent.futures.as_completed(futures):
            file, output_file = futures[future]
            
            try:
                if future.result():
                    stats['success'] += 1
                    if Path(output_file).exists():
                        stats['converted_size_total'] += Path(output_file).stat().st_size / 1024 / 1024
                    stats['original_size_total'] += Path(file).stat().st_size / 1024 / 1024 if Path(file).exists() else 0
                    processed.add(file)
                else:
                    stats['failed'] += 1
            except Exception as e:
                logging.error(f"Kritischer Fehler: {e}")
                stats['failed'] += 1
            
            if HAS_TQDM:
                file_iterator.update(1)
            
            save_resume_state(processed)
    
    stats['total_time'] = time.time() - start_total
    if stats['original_size_total'] > 0:
        stats['compression_percent'] = (1 - stats['converted_size_total'] / stats['original_size_total']) * 100
    
    # Report erstellen
    if config['logging'].get('create_report') and not args.no_report:
        Path(config['directories']['logs']).mkdir(exist_ok=True)
        create_report(stats, config, log_file)
    
    # Cleanup
    if stats['success'] > 0:
        RESUME_FILE.unlink(missing_ok=True)
    
    # Zusammenfassung
    logging.info("=" * 70)
    logging.info("=== ZUSAMMENFASSUNG ===")
    logging.info(f"Dateien: {stats['success'] + stats['failed']} gesamt")
    logging.info(f"✓ Erfolgreich: {stats['success']}")
    logging.info(f"✗ Fehlgeschlagen: {stats['failed']}")
    logging.info(f"Speicherersparnis: {stats['compression_percent']:.1f}%")
    logging.info(f"Gesamtdauer: {timedelta(seconds=int(stats['total_time']))}")
    logging.info("=" * 70)
    
    return 0 if stats['failed'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
