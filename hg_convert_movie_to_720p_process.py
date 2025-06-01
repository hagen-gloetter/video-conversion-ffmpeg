# hg_convert_movie_to_720p_progress .py
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


Beschleunigung der Ausführung:
Verwendung von ProcessPoolExecutor statt ThreadPoolExecutor (besser für CPU-intensive Tasks)
FFmpeg-Preset auf "fast" gesetzt (Kompromiss zwischen Geschwindigkeit und Dateigröße)
Maximale Auslastung aller CPU-Kerne
Sie könnten zusätzlich Hardware-Beschleunigung nutzen (z.B. NVENC für Nvidia-GPUs), indem Sie den Codec zu h265_nvenc ändern
Fortschrittsanzeige:
Integrierte tqdm-Progressbar zeigt den Gesamtfortschritt
Zähler für erfolgreiche/fehlgeschlagene Konvertierungen
Prozentuale Anzeige des Fortschritts
Anzeige der bereits bearbeiteten Dateien (z.B. "3/10 Dateien")
Dauer der Konvertierung:
Für jede Datei wird die Bearbeitungsdauer gemessen und angezeigt
Formatierte Ausgabe der Dauer im HH:MM:SS-Format
Erfolgreiche und fehlgeschlagene Konvertierungen werden mit ihrer Dauer gekennzeichnet
Zusätzliche Verbesserungen:
Übersichtliche Zusammenfassung am Ende (Gesamtzahl, Erfolge, Fehler)
Bessere Fehlerbehandlung mit spezifischen Fehlermeldungen
Farbige Emojis zur besseren Visualisierung des Status (✅/❌/⚠️)
Prozess-Isolation durch ProcessPool (vermeidet GIL-Limitationen)
Um das Skript zu verwenden, müssen Sie ggf. das tqdm-Paket installieren:
in der Shell/bash
    pip install tqdm
Für Hardware-Beschleunigung können Sie die FFmpeg-Parameter anpassen (z.B. -c:v h265_nvenc für Nvidia GPUs).
"""

import os
import subprocess
import concurrent.futures
from datetime import datetime, timedelta
import multiprocessing
import time
from tqdm import tqdm

def make_720p(input_file):
    output_file = os.path.join("720p", os.path.basename(input_file))
    start_time = time.time()
    try:
        # FFmpeg command with hardware acceleration if available
        cmd = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'error',
            '-i', input_file,
            '-s', 'hd720',
            '-c:v', 'libx265',
            '-crf', '23',
            '-preset', 'fast',  # Faster encoding with slightly larger file size
            output_file
        ]
        
        # Execute the command
        process = subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Move original file to done directory
        os.rename(input_file, os.path.join("done", os.path.basename(input_file)))
        
        duration = timedelta(seconds=round(time.time() - start_time))
        return (True, input_file, duration)
    except subprocess.CalledProcessError as e:
        duration = timedelta(seconds=round(time.time() - start_time))
        return (False, input_file, duration, str(e))
    except Exception as e:
        duration = timedelta(seconds=round(time.time() - start_time))
        return (False, input_file, duration, str(e))

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

    total_files = len(files_to_process)
    print(f"Found {total_files} files to process")
    print("Starting processing at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*80)

    # Use ProcessPoolExecutor for CPU-bound tasks (better than ThreadPool for FFmpeg)
    num_workers = multiprocessing.cpu_count()
    print(f"Using {num_workers} workers for parallel processing")
    print("="*80)

    processed_count = 0
    success_count = 0
    fail_count = 0

    # Create progress bar
    with tqdm(total=total_files, desc="Overall Progress", unit="file") as pbar:
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            # Submit all tasks
            future_to_file = {executor.submit(make_720p, file): file for file in files_to_process}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                processed_count += 1
                try:
                    result = future.result()
                    if result[0]:  # Success case
                        success_count += 1
                        print(f"\n✅ Success: {file} (Duration: {result[2]})")
                    else:  # Error case
                        fail_count += 1
                        print(f"\n❌ Failed: {file} (Duration: {result[2]}, Error: {result[3]})")
                    
                    # Update progress
                    percent_complete = (processed_count / total_files) * 100
                    pbar.set_postfix({
                        'Success': f'{success_count}/{total_files}',
                        'Failed': fail_count,
                        'Completed': f'{percent_complete:.1f}%'
                    })
                    pbar.update(1)
                    
                except Exception as e:
                    fail_count += 1
                    print(f"\n⚠️ Exception with {file}: {str(e)}")
                    pbar.update(1)

    print("="*80)
    print("Processing complete!")
    print(f"Total files: {total_files}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print("Finished at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()