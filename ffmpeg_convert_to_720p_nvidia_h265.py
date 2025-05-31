import os
import subprocess
from pathlib import Path
import argparse

def convert_video(input_path, output_path):
    """Konvertiert Video zu 720p mit HEVC-NVENC und optimaler Kompression"""
    try:
        cmd = [
            'ffmpeg',
            '-y',
            '-hwaccel', 'cuda',          # GPU-Beschleunigung
            '-i', str(input_path),
            '-vf', 'scale=-1:720',      # Automatische Skalierung bei 720p Höhe
            '-c:v', 'hevc_nvenc',       # HEVC/H.265 über GPU
            '-cq', '23',                # Visuelle Qualität (0-51, niedriger = besser)
            '-preset', 'slow',          # Beste Kompression
            '-tune', 'hq',              # High-Quality-Modus
            '-x265-params', 'psy-rd=2', # Psycho-visuelle Optimierungen
            '-c:a', 'copy',             # Audio unverändert
            '-map_metadata', '0',       # Metadaten erhalten
            str(output_path)
        ]
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Fehler bei {input_path.name}: {e.stderr.decode()}")
        return False

def process_folder(input_folder=None):
    """Verarbeitet alle Videos im Ordner"""
    input_folder = Path(input_folder) if input_folder else Path.cwd()
    
    output_folder = input_folder / '720p'
    done_folder = input_folder / 'done'
    
    output_folder.mkdir(exist_ok=True)
    done_folder.mkdir(exist_ok=True)
    
    video_files = [
        f for f in input_folder.glob('*.*') 
        if f.suffix.lower() in ('.mp4', '.mov', '.mkv', '.wmv')
        and not f.name.startswith('.')
    ]
    
    if not video_files:
        print("Keine unterstützten Video-Dateien gefunden.")
        return
    
    print(f"Starte HEVC-Konvertierung (GPU) für {len(video_files)} Videos...")
    
    for video in video_files:
        output_file = output_folder / f"720p_{video.stem}.mp4"
        if convert_video(video, output_file):
            video.rename(done_folder / video.name)
            print(f"✔ {video.name} → {output_file.name}")
    
    print("Fertig! Alle Videos wurden optimiert komprimiert.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video-Konvertierung zu 720p mit HEVC-NVENC")
    parser.add_argument('--input', help="Eingabeordner (optional)", default=None)
    args = parser.parse_args()
    
    process_folder(args.input)