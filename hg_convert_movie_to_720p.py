# hg_convert_movie_to_720p.py
# -*- coding: utf-8 -*-
# hg 2025-06-01

"""
Dieses Skript konvertiert Videodateien in 720p Auflösung mit dem libx265 Codec.
Es nutzt FFmpeg für die Konvertierung und verarbeitet alle unterstützten Videoformate in einem Verzeichnis.
Es erstellt zwei Unterverzeichnisse: "720p" für die konvertierten Dateien und "done" für die Originaldateien.

Wichtige Merkmale dieser Implementierung:
Parallele Verarbeitung: Das Skript nutzt ThreadPoolExecutor, um alle verfügbaren CPU-Kerne optimal auszulasten.
Dynamische Worker-Anzahl: Es ermittelt automatisch die Anzahl der verfügbaren Prozessoren mit multiprocessing.cpu_count().
Asynchrone Verarbeitung: Sobald ein Thread fertig ist, wird sofort der nächste gestartet.
Fehlerbehandlung: Robustes Exception-Handling für FFmpeg-Prozesse und Dateioperationen.
Fortschrittsanzeige: Gibt den Verarbeitungsstatus jedes Files aus.
Kommandozeilen-Sicherheit: Verwendet subprocess.run() mit korrektem Argument-Handling.
Verzeichnis-Handling: Erstellt die benötigten Verzeichnisse (720p, done) automatisch.
Logging: Zeigt Start- und Endzeit der Verarbeitung an.
Um das Skript zu verwenden, einfach im Verzeichnis mit den Video-Dateien ausführen. Es verarbeitet alle Dateien mit den Endungen .mp4, .wmv, .mov und .mkv.
Beachten Sie, dass FFmpeg mit libx265 installiert sein muss. Bei Problemen können Sie den Codec auf libx264 ändern, falls nötig.
"""
import os
import subprocess
import concurrent.futures
from datetime import datetime
import multiprocessing

def make_720p(input_file):
    output_file = os.path.join("720p", os.path.basename(input_file))
    try:
        # FFmpeg command with libx265 codec and 720p resolution
        cmd = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'error',
            '-i', input_file,
            '-s', 'hd720',
            '-c:v', 'libx265',
            '-crf', '23',
            output_file
        ]
        
        # Execute the command
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Move original file to done directory
        os.rename(input_file, os.path.join("done", os.path.basename(input_file)))
        
        print(f"Successfully processed: {input_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_file}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error with {input_file}: {e}")
        return False

def main():
    # Create directories if they don't exist
    os.makedirs("720p", exist_ok=True)
    os.makedirs("done", exist_ok=True)

    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("ffmpeg found")
    except:
        print("ffmpeg NOT found")
        exit(1)

    # Supported file extensions
    extensions = ('.mp4', '.wmv', '.mov', '.mkv')
    files_to_process = [f for f in os.listdir('.') if os.path.isfile(f) and f.lower().endswith(extensions)]

    if not files_to_process:
        print("No video files found to process.")
        return

    print(f"Found {len(files_to_process)} files to process")
    print("Starting processing at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*80)

    # Use ThreadPoolExecutor to parallelize the processing
    # Using all available CPU cores
    num_workers = multiprocessing.cpu_count()
    print(f"Using {num_workers} workers for parallel processing")

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(make_720p, file): file for file in files_to_process}
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                future.result()
            except Exception as e:
                print(f"Exception occurred while processing {file}: {e}")

    print("="*80)
    print("Finished processing at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()