#!/bin/bash
# install_ubuntu.sh - Ubuntu 22.04 / 24.04 LTS Installation
# Installiert alle erforderlichen Abhängigkeiten für Video-Konvertierung

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Video-Konvertierung Installation ===${NC}"
echo "Ubuntu 22.04 / 24.04 LTS"
echo

# Prüfe ob root/sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}[ERROR]${NC} Dieses Script muss mit sudo ausgeführt werden!"
    echo "Nutzung: sudo bash install_ubuntu.sh"
    exit 1
fi

echo -e "${YELLOW}[1/3]${NC} Aktualisiere Paketquellen..."
apt-get update

echo -e "${YELLOW}[2/3]${NC} Installiere FFmpeg mit Video-Encodern..."
apt-get install -y \
    ffmpeg \
    libx265-dev \
    libx264-dev

echo -e "${YELLOW}[3/3]${NC} Installiere Python 3 (falls nicht vorhanden)..."
apt-get install -y \
    python3 \
    python3-minimal

# Verifizierung
echo
echo -e "${BLUE}=== Verifizierung ===${NC}"

if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}[✓]${NC} FFmpeg installiert:"
    ffmpeg -version | head -n 1
else
    echo -e "${RED}[✗]${NC} FFmpeg Fehler"
    exit 1
fi

if command -v python3 &> /dev/null; then
    echo -e "${GREEN}[✓]${NC} Python 3 installiert:"
    python3 --version
else
    echo -e "${RED}[✗]${NC} Python 3 Fehler"
    exit 1
fi

# Prüfe Encoder-Verfügbarkeit
echo -e "${BLUE}=== Verfügbare Video-Encoder ===${NC}"
if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "libx265"; then
    echo -e "${GREEN}[✓]${NC} libx265 (H.265/HEVC) verfügbar"
else
    echo -e "${YELLOW}[!]${NC} libx265 nicht gefunden"
fi

if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "libx264"; then
    echo -e "${GREEN}[✓]${NC} libx264 (H.264) verfügbar"
else
    echo -e "${RED}[✗]${NC} libx264 nicht gefunden"
fi

echo
echo -e "${BLUE}=== Installation abgeschlossen! ===${NC}"
echo
echo -e "${YELLOW}Nächste Schritte:${NC}"
echo "1. Navigiere zum Projektverzeichnis:"
echo "   cd /path/to/video-conversion-ffmpeg"
echo
echo "2. Mache Scripts ausführbar:"
echo "   chmod +x *.sh"
echo
echo "3. Starte Konvertierung (Python):"
echo "   python3 hg_convert_movie_to_720p.py /pfad/zu/videos"
echo
echo "   oder (Bash):"
echo "   ./hg_convert_movie_to_720p.sh /pfad/zu/videos"
echo
echo "4. Konfiguriere bei Bedarf die Qualität in den Scripts (CRF_VALUE, PRESET)"
echo
