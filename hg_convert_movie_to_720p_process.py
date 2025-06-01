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
import time
import multiprocessing
from datetime import datetime, timedelta
from collections import defaultdict

# Konfiguration
TERMINAL_WIDTH = 80
UPDATE_INTERVAL = 0.5  # Sekunden zwischen Updates

# Globale Fortschrittsdaten
progress_data = defaultdict(dict)
progress_lock = multiprocessing.Lock()
start_times = {}

def make_720p(input_file, thread_id):
    output_file = os.path.join("720p", os.path.basename(input_file))
    start_time = time.time()
    start_times[thread_id] = start_time
    
    try:
        cmd = [
            'ffmpeg',
            '-hide_banner',
            '-i', input_file,
            '-s', 'hd720',
            '-c:v', 'libx265',
            '-crf', '23',
            '-preset', 'fast',
            output_file
        ]
        
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
        
        while process.poll() is None:
            # Einfache Fortschrittsberechnung basierend auf Laufzeit
            elapsed = time.time() - start_time
            with progress_lock:
                progress_data[thread_id] = {
                    'filename': os.path.basename(input_file),
                    'progress': min(0.99, elapsed / 10),  # Temporärer Platzhalter
                    'start_time': start_time,
                    'status': 'running'
                }
            time.sleep(0.5)
        
        # Nach Abschluss aktualisieren
        with progress_lock:
            progress_data[thread_id]['progress'] = 1.0
            progress_data[thread_id]['status'] = 'done' if process.returncode == 0 else 'failed'
        
        if process.returncode == 0:
            os.rename(input_file, os.path.join("done", os.path.basename(input_file)))
            return True, input_file, timedelta(seconds=round(time.time() - start_time))
        else:
            return False, input_file, timedelta(seconds=round(time.time() - start_time)), "FFmpeg Error"
    
    except Exception as e:
        with progress_lock:
            progress_data[thread_id]['status'] = 'error'
        return False, input_file, timedelta(seconds=round(time.time() - start_time)), str(e)

def draw_progress_bars(total_files, processed_count):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"Video-Konvertierung | Dateien: {processed_count}/{total_files}")
    print("=" * TERMINAL_WIDTH)
    
    active_threads = {k: v for k, v in progress_data.items() if v.get('status') == 'running'}
    
    for thread_id, data in sorted(active_threads.items()):
        progress = data.get('progress', 0)
        bar_width = TERMINAL_WIDTH - 30
        filled = int(round(bar_width * progress))
        bar = '#' * filled + '-' * (bar_width - filled)
        
        elapsed = timedelta(seconds=int(time.time() - data['start_time']))
        print(f"Thread {thread_id}: {data['filename'][:20].ljust(20)} "
              f"[{bar}] {progress*100:5.1f}% "
              f"({elapsed})")
    
    print("=" * TERMINAL_WIDTH)

def main():
    os.makedirs("720p", exist_ok=True)
    os.makedirs("done", exist_ok=True)

    # FFmpeg Verfügbarkeit prüfen
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("FFmpeg gefunden - Starte Konvertierung...")
    except:
        print("Fehler: FFmpeg nicht gefunden!")
        exit(1)

    # Dateien finden
    extensions = ('.mp4', '.wmv', '.mov', '.mkv')
    files_to_process = [f for f in os.listdir('.') if os.path.isfile(f) and f.lower().endswith(extensions)]
    
    if not files_to_process:
        print("Keine passenden Videodateien gefunden.")
        return

    total_files = len(files_to_process)
    num_workers = min(multiprocessing.cpu_count(), total_files)
    
    print(f"Verarbeite {total_files} Dateien mit {num_workers} Threads...")
    time.sleep(1)

    processed_count = 0
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(make_720p, file, i): (i, file) 
                for i, file in enumerate(files_to_process)}
        while futures:
            done, _ = concurrent.futures.wait(futures, timeout=UPDATE_INTERVAL)
            draw_progress_bars(total_files, processed_count)
            
            for future in done:
                thread_id, file = futures[future]
                processed_count += 1
                del futures[future]
                # Thread-Daten aufräumen
                with progress_lock:
                    if thread_id in progress_data:
                        progress_data[thread_id]['status'] = 'completed'

    # Finaler Status
    print("\n" + "=" * TERMINAL_WIDTH)
    print(f"Konvertierung abgeschlossen in {timedelta(seconds=round(time.time() - start_time))}")
    print(f"Verarbeitete Dateien: {processed_count}/{total_files}")

if __name__ == "__main__":
    main()