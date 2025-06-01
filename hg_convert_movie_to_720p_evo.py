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
Individuelle Fortschrittsbalken:
Jeder Thread bekommt seinen eigenen Balken aus # Zeichen
Balkenlänge entspricht dem Fortschritt (0-100%)
Klare Zuordnung durch Thread-ID
Echtzeit-Update:
Terminal wird regelmäßig aktualisiert (1x pro Sekunde)
FFmpeg liefert Fortschrittsdaten über pipe
Thread-sichere Updates mit Lock-Mechanismus
Zusätzliche Informationen:
Gesamtfortschritt (x/y Dateien)
Erfolgs-/Fehlerstatistik
Verarbeitungsdauer pro Datei
Performance-Optimierungen:
ThreadPoolExecutor für parallele Verarbeitung
Dynamische Terminalbreite
Regelmäßiges Clearing für übersichtliche Anzeige
Anmerkungen:
Die Fortschrittsberechnung ist vereinfacht (basierend auf der Zeit)
Für genauere Fortschrittsanzeige müsste man die Gesamtdauer der Datei kennen
Das Terminal-Clearing funktioniert am besten unter Linux/macOS
Bei Windows ggf. os.system('cls') verwenden
"""
import os
import subprocess
import concurrent.futures
from datetime import datetime, timedelta
import multiprocessing
import time
import sys
from collections import defaultdict

# Globale Variablen für Fortschrittsanzeige
progress_bars = defaultdict(float)
progress_lock = multiprocessing.Lock()
terminal_width = 80

def make_720p(input_file, thread_id):
    global progress_bars
    output_file = os.path.join("720p", os.path.basename(input_file))
    start_time = time.time()
    
    try:
        # FFmpeg command mit Progress-Reporting
        cmd = [
            'ffmpeg',
            '-hide_banner',
            '-i', input_file,
            '-s', 'hd720',
            '-c:v', 'libx265',
            '-crf', '23',
            '-preset', 'fast',
            '-progress', 'pipe:1',  # FFmpeg Fortschritt als stdout
            output_file
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        while True:
            line = process.stdout.readline()
            if line == '' and process.poll() is not None:
                break
            if 'out_time_ms' in line:
                # Fortschritt aktualisieren
                with progress_lock:
                    progress_bars[thread_id] = float(line.split('=')[1]) / 1e7  # Vereinfachte Fortschrittsberechnung
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
        
        os.rename(input_file, os.path.join("done", os.path.basename(input_file)))
        duration = timedelta(seconds=round(time.time() - start_time))
        return (True, input_file, duration)
    
    except Exception as e:
        duration = timedelta(seconds=round(time.time() - start_time))
        return (False, input_file, duration, str(e))

def draw_progress_bars(total_files, processed_count):
    os.system('cls' if os.name == 'nt' else 'clear')  # Terminal leeren
    
    print(f"Verarbeite {total_files} Dateien | Fertig: {processed_count}/{total_files}")
    print("=" * terminal_width)
    
    # Sortierte Liste der Threads für konsistente Anzeige
    sorted_threads = sorted(progress_bars.keys())
    
    for thread_id in sorted_threads:
        progress = progress_bars[thread_id]
        bar_width = terminal_width - 20
        filled = int(round(bar_width * progress))
        bar = '#' * filled + '-' * (bar_width - filled)
        print(f"Thread {thread_id}: [{bar}] {progress*100:.1f}%")
    
    print("=" * terminal_width)

def main():
    os.makedirs("720p", exist_ok=True)
    os.makedirs("done", exist_ok=True)

    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("ffmpeg gefunden")
    except:
        print("ffmpeg NICHT gefunden")
        exit(1)

    extensions = ('.mp4', '.wmv', '.mov', '.mkv')
    files_to_process = [f for f in os.listdir('.') if os.path.isfile(f) and f.lower().endswith(extensions)]

    if not files_to_process:
        print("Keine Videodateien gefunden.")
        return

    total_files = len(files_to_process)
    num_workers = multiprocessing.cpu_count()
    
    print(f"Starte Verarbeitung von {total_files} Dateien mit {num_workers} Threads")
    print("=" * terminal_width)

    processed_count = 0
    success_count = 0
    fail_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(make_720p, file, i % num_workers): file 
                for i, file in enumerate(files_to_process)}
        
        while True:
            done, not_done = concurrent.futures.wait(futures, timeout=1)
            
            # Fortschrittsbalken zeichnen
            draw_progress_bars(total_files, processed_count)
            
            for future in done:
                file = futures[future]
                processed_count += 1
                try:
                    result = future.result()
                    if result[0]:
                        success_count += 1
                        print(f"✅ {file} erfolgreich in {result[2]}")
                    else:
                        fail_count += 1
                        print(f"❌ {file} fehlgeschlagen ({result[3]})")
                except Exception as e:
                    fail_count += 1
                    print(f"⚠️ Unerwarteter Fehler bei {file}: {str(e)}")
                
                del futures[future]
            
            if not futures:
                break

    print("\n" + "=" * terminal_width)
    print(f"Verarbeitung abgeschlossen! Erfolgreich: {success_count}, Fehlgeschlagen: {fail_count}")
    print(f"Gesamtzeit: {timedelta(seconds=round(time.time() - start_time))}")

if __name__ == "__main__":
    start_time = time.time()
    main()