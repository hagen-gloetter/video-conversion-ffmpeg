import os
import subprocess
from pathlib import Path
from multiprocessing import Pool, cpu_count
import shutil

def convert_to_720p_cpu(args):
    """Konvertiert ein Video zu 720p mit CPU (libx265)"""
    input_path, output_path = args
    try:
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', 'scale=-1:720',
            '-c:v', 'libx265',
            '-crf', '23',               # Qualitätsstufe (0-51, 23 ist Standard)
            '-preset', 'slow',      # -preset slow	Geschwindigkeit/Kompression	fast, medium, slow
            '-c:a', 'copy',
            '-map_metadata', '0',
            '-movflags', 'use_metadata_tags',
            output_path
        ]
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        return (input_path, output_path, True)
    except subprocess.CalledProcessError as e:
        return (input_path, output_path, False, e.stderr.decode())

def process_videos(input_folder='.'):
    # Ordner erstellen
    output_folder = os.path.join(input_folder, '720p')
    done_folder = os.path.join(input_folder, 'done')
    
    Path(output_folder).mkdir(exist_ok=True)
    Path(done_folder).mkdir(exist_ok=True)
    
    # MP4-Dateien finden
    files_to_process = [
        (os.path.join(input_folder, f), os.path.join(output_folder, f"720p_{f}"))
        for f in os.listdir(input_folder) 
        if f.lower().endswith('.mp4') and not f.startswith('.')
    ]
    
    if not files_to_process:
        print("Keine MP4-Videos gefunden.")
        return
    
    print(f"Starte Konvertierung (CPU) auf {cpu_count()} Kernen...")
    
    with Pool(processes=cpu_count()) as pool:
        results = pool.imap_unordered(convert_to_720p_cpu, files_to_process)
        
        for result in results:
            input_path, output_path, success, *error = result
            filename = os.path.basename(input_path)
            print(f"filename: {filename}")
            if success:
                shutil.move(input_path, os.path.join(done_folder, filename))
                print(f"✔ {filename} (erfolgreich)")
            else:
                print(f"✖ Fehler bei {filename}: {error[0] if error else 'Unbekannter Fehler'}")
    
    print("Alle Videos wurden verarbeitet.")

if __name__ == "__main__":
    process_videos()