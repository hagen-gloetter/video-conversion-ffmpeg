# 🎬 Video Conversion FFmpeg - Professional Edition

Professionelle Videokonvertierung zu 720p H.265 mit Hardware-Acceleration, Config-Management, Progress-Tracking und erweiterten Features.

**Neueste Version**: Session 2.2 (2026-03-30) - Standalone-Modus! 🚀

---

## ⭐ Was ist neu in Session 2.2?

✅ **100% Standalone** - Skripte funktionieren ohne zusätzliche Dateien  
✅ **Parameter im Code** - Inline-Parameter für einfaches Kopieren  
✅ **config.yaml optional** - Nur für Personalisierung  
✅ **Einfaches Deployment** - Skript in Zielordner kopieren, fertig  

**Vorher**: Script + config.yaml + requirements.txt  
**Nachher**: Ein Skript, fertig! (Optional: config.yaml + requirements.txt)

---

## 🚀 Quickstart - STANDALONE

### 1️⃣ Schnellstart (im Ordner mit Videos)
```bash
# Einfach kopieren und ausführen - das war's!
python3 hg_convert_movie_to_720p.py /mnt/videos/
```

Alle Videos im Ordner werden konvertiert! ✅

### 2️⃣ Optional: Parameter anpassen
Datei öffnen und bearbeiten:
```python
# hg_convert_movie_to_720p.py - oben in der Datei
OUTPUT_DIR = "720p"                     # Ziel-Verzeichnis
CRF_VALUE = 22                          # Qualität (22=besser, 20=sehr gut, etc.)
PRESET = "slow"                         # Geschwindigkeit
AUDIO_BITRATE = "128k"                  # Audio-Qualität
MAX_THREADS = auto (80% der CPU)        # Parallel-Threads
```

### 3️⃣ Optional: config.yaml für Override
```bash
# Wenn PyYAML installiert: config.yaml kann Parameter überschreiben
python3 hg_convert_movie_to_720p.py /mnt/videos/ --config config.yaml
```

---

## 📋 Features Overview

### Hardware-Beschleunigung
- 🍎 **Apple Silicon/Intel MAC**: `hevc_videotoolbox` (3x schneller)
- 🔷 **NVIDIA GPU**: `hevc_nvenc` (GPU-beschleunigt)
- 💻 **Software-Encoder**: `libx265` (beste Kompression)
- ⚙️ **Fallback**: `libx264` (universelle Kompatibilität)

### Intelligente Funktionalität
- 🔄 **Auto Encoder-Erkennung** mit Fallback-Chain
- 📊 **Komputation**: Echte Größenersparnis-Berechnung
- 🛡️ **Fehlerbehandlung**: Retry-Logik mit Timeout
- ⏸️ **Resume**: Unterbrechbare Konvertierungen
- 🎯 **Intelligente Skalierung**: Erhält Aspect-Ratio
- 📈 **Detailliertes Logging**: Console + File + Report

---

## 🎯 Verwendungsszenarien

### Szenario 1: Schnelle Konvertierung
```bash
python3 hg_convert_movie_to_720p.py /mnt/videos/ --preset fast
# 45-50% Größenersparnis, 3x schneller!
```

### Szenario 2: Beste Qualität
```bash
python3 hg_convert_movie_to_720p.py /mnt/videos/ --preset ultra
# 65-70% Größenersparnis, beste Qualität, aber 4x langsamer
```

### Szenario 3: Test ohne echte Konvertierung  
```bash
python3 hg_convert_movie_to_720p.py /mnt/videos/ --dry-run
# Zeigt was würde konvertiert ohne es zu tun
```

### Szenario 4: Nur große Dateien
```bash
python3 hg_convert_movie_to_720p.py /mnt/videos/ --min-size 500 --preset high_quality
# Nur Dateien >500MB, beste Qualität
```

### Szenario 5: Format ausschließen
```bash
python3 hg_convert_movie_to_720p.py /mnt/videos/ --exclude flv wmv
# Ignoriere .flv und .wmv Dateien
```

---

## 📥 Installation

### Ubuntu 22.04 / 24.04 LTS
```bash
sudo bash install_ubuntu.sh
```

### macOS  
```bash
brew install ffmpeg python3
pip3 install -r requirements.txt  # Optional: für tqdm & config.yaml
```

### Alle Systeme
```bash
# Nur FFmpeg erforderlich!
ffmpeg -version  # Prüfe Installation
```

---

## 📊 Quality Presets

| Preset | CRF | Größenersparnis | Geschwindigkeit | Verwendung |
|--------|-----|-----------------|-----------------|-----------|
| **fast** | 24 | 45-50% | 3x schneller | Schnelle Batch-Verarbeitung |
| **balanced** (default) | 22 | 55-60% | Standard | Allzweck-Konvertierung |
| **high_quality** | 20 | 60-65% | 2x langsamer | Archivierung, wichtige Videos |
| **ultra** | 18 | 65-70% | 4x+ langsamer | Maximale Qualität |

---

## 🔧 CLI Arguments

```bash
python3 hg_convert_movie_to_720p.py [PFAD] [OPTIONS]

Options:
  PFAD                  Verzeichnis mit Videodateien; nur PFAD aktiviert Automatik
  --preset {fast|balanced|high_quality|ultra}
                        Qualitäts-Preset
  --dry-run             Zeige was würde konvertiert ohne zu konvertieren
  --min-size MB         Nur Dateien größer als X MB
  --min-res HEIGHT      Nur Dateien mit mind. X px Höhe
  --exclude ext1 ext2   Ignoriere Dateiformate (z.B. flv wmv)
  --resume              Fortfahren mit unterbrochener Konvertierung
  --config YAML         Path zu custom config.yaml
  --help                Diese Hilfe
```

---

## 🎬 Skripte Übersicht

| Skript | Funktion | Besonderheit |
|--------|----------|---|
| **hg_convert_movie_to_720p.py** | Alle Formate + CLI | Einzige Python-Version, Automatik bei Pfad-only-Aufruf |
| **convert.sh** | Bash-Version | Shell-Script, STANDALONE |
| **convert_flv.sh** | FLV→MP4 speziell | Format-spezifisch, STANDALONE |
| **convert_wmv.sh** | WMV→MP4 speziell | Format-spezifisch, STANDALONE |
| **hg_convert_movie_to_720p.sh** | Parallel-Bash | Alle Videos parallel, STANDALONE |

---

## 📈 Performance (M4 Mac Benchmark)

**Ohne Hardware-Acceleration**: libx265 ~100s/GB  
**Mit hevc_videotoolbox**: ~30s/GB ✅ **3.3x schneller!**

**Ubuntu Linux**: libx265 ~120s/GB  
**Ubuntu + NVIDIA**: hevc_nvenc ~40s/GB ✅ **3x schneller!**

---

## 🐳 Docker Deployment

```bash
# Build Image
docker build -t video-converter .

# Oder einfach compose
docker-compose up

# Mit Custom Config
docker run -v $(pwd)/videos:/data -v $(pwd)/config.yaml:/app/config.yaml video-converter
```

---

## 📂 Dateistruktur

```
video-conversion-ffmpeg/
├── hg_convert_movie_to_720p.py      ← Einzige Python-Version (alle Features + Automatik)
├── hg_convert_movie_to_720p.sh      ← Parallel (Bash, multi-threaded)
├── convert.sh                        ← Basic (Bash, universell)
├── convert_flv.sh                    ← FLV-spezifisch (Bash)
├── convert_wmv.sh                    ← WMV-spezifisch (Bash)
├── config.yaml                       ← Optional: Config-Overrides
├── requirements.txt                  ← Optional: Python Dependencies
├── install_ubuntu.sh                 ← Ubuntu Installer
├── Dockerfile                        ← Docker Image
├── docker-compose.yml                ← Docker Compose
├── README.md                         ← Diese Datei
├── CHANGELOG.md                      ← Version History
└── LICENSE                           ← GPL v3
```

---

## 🌍 System-Kompatibilität

✅ **Ubuntu 22.04 / 24.04 LTS**  
✅ **Debian 11 / 12**  
✅ **macOS Intel & Apple Silicon**  
⚠️ **Windows**: Via WSL2 (Ubuntu)  
⚠️ **CentOS/RedHat**: Nur mit community FFmpeg builds

---

## 🚀 Advanced Features (Python)

### 1. Resume nach Unterbruch
```bash
# Job unterbrechen (Ctrl+C ist ok)
python3 hg_convert_movie_to_720p.py /mnt/videos/

# Später weitermachen
python3 hg_convert_movie_to_720p.py /mnt/videos/ --resume
```

### 2. Statistik-Reports
Automatisch generiert nach Konvertierung:
- `logs/conversion_YYYY-MM-DD_HH-MM-SS.log` → Text-Log
- `logs/report_YYYY-MM-DD.json` → JSON-Report mit Stats

### 3. Video-Info vor Konvertierung
```bash
# Zeigt automatisch: Auflösung, Codec, Dauer
ffprobe videos/input.mp4 
```

### 4. Parallel-Verarbeitung
Nutzt 80% der CPU für mehrere Videos gleichzeitig.

---

## 🔑 Häufige Anpassungen

### Andere Auflösung (z.B. 1080p statt 720p)
```python
# In hg_convert_movie_to_720p.py ändern:
SCALE_FILTER = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
```

### Höhere Qualität als ultra
```python
# CRF-Wert kleiner machen (0=beste): CRF_VALUE = 16
```

### Andere Audio-Bitrate  
```python
AUDIO_BITRATE = "192k"  # oder 256k, 320k, etc.
```

---

## 🐛 Troubleshooting

| Problem | Lösung |
|---------|--------|
| `ffmpeg: command not found` | `sudo apt-get install ffmpeg` (oder brew) |
| `No suitable encoder found` | Siehe Sections "Hardware-Acceleration" |
| `ModuleNotFoundError: yaml` | `pip3 install pyyaml` (optional) |
| `Converting very slowly` | Nutze `--preset fast` oder bessere Hardware |
| `Converted file seems broken` | Prüfe: `ffmpeg -i OUTPUT.mp4 -f null -` |

---

## 📞 Support

**Issues**: Logs in `logs/` Verzeichnis prüfen  
**Tests**: `--dry-run` um Einstellungen zu testen  
**Config**: `config.yaml` nur bei Bedarf bearbeiten  

---

## 📄 Lizenz

GPL v3.0 - Siehe [LICENSE](LICENSE)

# Nur hochauflösende Videos (>=1080p)
python3 hg_convert_movie_to_720p.py /mnt/videos/ --min-res 1080

# Bestimmte Formate ausschließen
python3 hg_convert_movie_to_720p.py /mnt/videos/ --exclude mov flv

# Kombiniert
python3 hg_convert_movie_to_720p.py /mnt/videos/ --preset fast --min-size 50 --dry-run

# Weitermachen nach Unterbruch
python3 hg_convert_movie_to_720p.py /mnt/videos/ --resume
```

### Docker

```bash
# Bauen
docker build -t video-converter .

# Einfache Nutzung
docker run -v $(pwd)/videos:/data video-converter

# Mit compose
docker-compose up

# Mit Optionen
docker-compose run video-converter --preset fast --dry-run
```

---

## 📁 Dateistruktur nach Update

```
video-conversion-ffmpeg/
├── hg_convert_movie_to_720p.py         ← Python: Voll-Features Version
├── convert.sh                           ← Bash Universal
├── convert_flv.sh                       ← Bash FLV-spezifisch
├── convert_wmv.sh                       ← Bash WMV-spezifisch
├── hg_convert_movie_to_720p.sh          ← Bash Parallel
│
├── config.yaml                          ← ✨ NEU: Zentrale Konfiguration
├── requirements.txt                     ← ✨ NEU: Python-Abhängigkeiten
├── install_ubuntu.sh                    ← Auto-Installation
│
├── Dockerfile                           ← ✨ NEU: Docker-Container
├── docker-compose.yml                   ← ✨ NEU: Docker Compose
├── .dockerignore                        ← ✨ NEU: Docker-Ignores
│
├── README.md                            ← Diese Datei
├── CHANGELOG.md                         ← Änderungs-Dokumentation
├── LICENSE                              ← GPL v3
│
└── [input-videos]/                      ← Hier Videodateien platzieren
```

---

## ⚙️ Konfiguration

### config.yaml - Zentrale Einstellungen

**Beispiel für schnelle Konvertierung**:

```yaml
encoding:
  crf_value: 24        # Schneller, etwas weniger Qualität
  preset: fast         # Schnelle Verarbeitung
  audio_bitrate: "128k"

parallel:
  cpu_usage: 1.0       # Nutze 100% der CPUs (aggressiver)
```

**Beispiel für maximale Qualität**:

```yaml
encoding:
  crf_value: 18        # Ultra-Qualität
  preset: veryslow     # Beste Kompression
  audio_bitrate: "256k"

presets:
  best:
    crf: 18
    preset: veryslow
```

### Quality Presets - Vordefiniert

| Preset | CRF | Speed | Kompression | Qualität | Nutzung |
|--------|-----|-------|-------------|----------|---------|
| `fast` | 24 | ⚡⚡⚡ 3x | 45-50% | Gut | Schnelle Bereinigung |
| `balanced` | 22 | ⚡⚡ Standard | 55-60% | Sehr gut | Standard (default) |
| `high_quality` | 20 | ⚡ Länger | 60-65% | Exzellent | Archivierung |
| `ultra` | 18 | 🐌 Sehr lang | 65-70% | Ultra | Maximale Qualität |

---

## 📊 Performance-Vergleich

### Hardware-Encoder Performance

| Methode | Geschwindigkeit | Kompression | Qualität | Best für |
|---------|-----------------|-------------|----------|----------|
| hevc_videotoolbox | 🚀 3x schneller | 55% | Gut | macOS, schnelle Batches |
| hevc_nvenc | 🚀 2x schneller | 58% | Sehr gut | Linux+NVIDIA |
| libx265 | ⏱️ 1x baseline | 60% | Exzellent | Beste Qualität, Archivierung |
| libx264 | ⏱️ 1x baseline | 45% | Gut | Kompatibilität |

### Präset-Vergleich (libx265)

```
Beispiel: 500 MB Video

fast:           180s  →  250 MB  (50% Ersparnis) ⚡⚡⚡
balanced:       480s  →  200 MB  (60% Ersparnis) ⚡⚡
high_quality:   900s  →  190 MB  (62% Ersparnis) ⚡
ultra:         2000s  →  175 MB  (65% Ersparnis) 🐌
```

---

## 📝 CLI Argumente

```bash
python3 hg_convert_movie_to_720p.py [PFAD] [OPTIONS]

Options:
  PFAD                 Verzeichnis mit Videos; nur PFAD aktiviert Automatik
  --preset {fast,balanced,high_quality,ultra}
                        Qualitäts-Preset verwenden
  --dry-run            Zeige was konvertiert würde (ohne echte Konvertierung)
  --min-size MB        Minimale Dateigröße (z.B. --min-size 100)
  --min-res PX         Minimale Videoauflösung Höhe (z.B. --min-res 1080)
  --exclude FORMAT     Formate ausschließen (z.B. --exclude mov flv)
  --resume             Fahre mit unterbrochener Konvertierung fort
  --no-report          Erstelle keinen Statistik-Report
  --config FILE        Pfad zu custom config.yaml
  -h, --help           Zeige Hilfe
```

---

## 📊 Output & Reporting

### Console Output

```
INFO - ✓ FFmpeg gefunden
INFO - 🍎 Hardware-Encoder: hevc_videotoolbox (Apple Silicon)
INFO - 📋 Preset verwendet: fast
INFO - 🔍 Gefunden: 5 Dateien
INFO - Konvertierung: 60%|██████░░░░| 3/5 [05:30<04:30, 95.2s per file]
INFO - ✓ video1.mov: 250MB → 150MB (40% Ersparnis, 45s)
INFO - 📊 Report erstellt: logs/report_2026-03-30_21-15-45.txt
```

### Report-Datei (TXT)

```
KONVERTIERUNGS-STATISTIK
======================================================================
Datum: 2026-03-30 21:30:45
Gesamtdauer: 0:23:45
Plattform: Darwin (macOS)
Encoder: hevc_videotoolbox

ERGEBNISSE
======================================================================
Dateien gesamt: 5
✓ Erfolgreich: 5 (100.0%)
✗ Fehlgeschlagen: 0

SPEICHERPLATZ
======================================================================
Original: 1250.5MB
Konvertiert: 500.2MB
Ersparnis: 60.0%

DURCHSCHNITTSWERTE
======================================================================
Zeit pro Datei: 285 Sekunden
Größe Original: 250.1MB
Größe Konvertiert: 100.0MB
```

### Resume-Funktion

```bash
# Wenn unterbrochen (Ctrl+C):
[INFO] Konvertierung unterbrochen...

# Später weitermachen:
python3 hg_convert_movie_to_720p.py /mnt/videos/ --resume
[INFO] Lade Resume-State...
[INFO] Gefunden: 5 Dateien (3 bereits verarbeitet, 2 verbleibend)
```

---

## 🔧 Fortgeschrittene Nutzung

### Mehrere Konfigurationen

```bash
# Erstelle verschiedene Configs
cp config.yaml config_fast.yaml
cp config.yaml config_hq.yaml

# Und nutze sie:
python3 hg_convert_movie_to_720p.py /mnt/videos/ --config config_fast.yaml
python3 hg_convert_movie_to_720p.py /mnt/videos/ --config config_hq.yaml
```

### Batch-Verarbeitung mit Filtern

```bash
# Nur große Dateien
python3 hg_convert_movie_to_720p.py /mnt/videos/ --min-size 500 --preset fast

# Nur HD-Videos
python3 hg_convert_movie_to_720p.py /mnt/videos/ --min-res 720

# Ausschließen von bestimmten Formaten
python3 hg_convert_movie_to_720p.py /mnt/videos/ --exclude flv wmv
```

### Docker mit Volume-Mounting

```bash
# Video-Verzeichnis mounten
docker run -v /home/user/videos:/data video-converter --preset fast

# Mit compose und custom config
docker-compose run -v extra_config.yaml:/app/config.yaml video-converter
```

---

## 📊 Skalierungs-Formel

Modern Skalierung mit Aspect-Ratio-Erhaltung:

```
scale=1280:720:force_original_aspect_ratio=decrease,
pad=1280:720:(ow-iw)/2:(oh-ih)/2
```

**Was das macht**:
1. **Scale**: Skaliert Video auf maximal 1280×720
2. **aspect_ratio=decrease**: Verhindert Vergrößerung
3. **pad**: Füllt leeren Raum mit schwarzen Balken
4. **Zentrierung**: Bild ist immer zentriert

**Ergebnis**: Keine Verzerrungen, perfekte Skalierung!

---

## 🛠️ Fallback-Mechanismus

Scripts wählen automatisch den besten Encoder:

```
┌─────────────────────────────────┐
│  Encoder-Auswahl-Hierarchie     │
└─────────────────────────────────┘
         ↓
┌─ macOS?
│  └─ hevc_videotoolbox? → NUTZE
│
├─ NVIDIA GPU?
│  └─ hevc_nvenc? → NUTZE
│
├─ libx265 verfügbar?
│  └─ JA → NUTZE
│
└─ FALLBACK
   └─ libx264 (universell)
```

Wenn Encoder fehlschlägt: **Automatisch nächster in der Chain**

---

## 📋 Skript-Optionen (Overviow/Vergleich)

| Feature | Python | Bash |
|---------|--------|------|
| config.yaml | ✅ | ⚠️ |
| Presets | ✅ | ⚠️ |
| Pfad-Parameter mit Automatik | ✅ | ✅ |
| Dry-run | ✅ | ❌ |
| Progress-Bar | ✅ | ❌ |
| Retry-Logik | ✅ | ❌ |
| ffprobe Info | ✅ | ❌ |
| Reports | ✅ | ❌ |
| Filtering | ✅ | ❌ |
| Resume | ✅ | ❌ | ❌ |
| Docker | ✅ | ⚠️ | ⚠️ |
| Parallelize | ✅ | ✅ | ✅ |
| Hardware-Accel | ✅ | ✅ | ✅ |

---

## 📜 Lizenz

GNU General Public License v3.0 - Siehe [LICENSE](LICENSE)

## 👤 Autor

Hagen Glötter  
hagen.gloetter@gmail.com  
**Updated**: 2026-03-30