import os
import subprocess
from pathlib import Path
import argparse
import sys

def convert_video(input_path, output_path):
    """Konvertiert ein Video zu 720p mit NVENC"""
    try:
        cmd = [
            'ffmpeg',
            '-y',
            '-hwaccel', 'cuda',
            '-i', str(input_path),
            '-vf', 'scale=1280:720',
            '-c:v', 'h264_nvenc',
            '-cq', '28',
            '-c:a', 'copy',
            '-map_metadata', '0',
            str(output_path)
        ]
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Fehler bei {input_path.name}: {e.stderr.decode()}")
        return False

def process_folder(input_folder=None):
    """Verarbeitet alle MP4s im Ordner"""
    # Aktuelles Verzeichnis als Default
    input_folder = Path(input_folder) if input_folder else Path.cwd()
    
    output_folder = input_folder / '720p'
    done_folder = input_folder / 'done'
    
    output_folder.mkdir(exist_ok=True)
    done_folder.mkdir(exist_ok=True)
    
    video_files = [
        f for f in input_folder.glob('*.mp4') 
        if not f.name.startswith('.')
    ]
    
    if not video_files:
        print("Keine MP4-Videos gefunden.")
        return
    
    print(f"Starte Konvertierung von {len(video_files)} Videos...")
    
    for video in video_files:
        output_file = output_folder / f"720p_{video.name}"
        if convert_video(video, output_file):
            video.rename(done_folder / video.name)
            print(f"✔ {video.name} erfolgreich konvertiert")
    
    print("Alle Videos verarbeitet.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', help="Eingabeordner (optional)", default=None)
    args = parser.parse_args()
    
    process_folder(args.input)