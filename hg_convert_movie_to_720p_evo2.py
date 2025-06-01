import os
import subprocess
import concurrent.futures
import time
import multiprocessing
from datetime import datetime, timedelta
from collections import defaultdict

# Konfiguration
TERMINAL_WIDTH = 80
UPDATE_INTERVAL = 0.3  # Sekunden zwischen Updates

# Fortschrittsdaten
progress_data = defaultdict(dict)
progress_lock = multiprocessing.Lock()

def get_duration(input_file):
    """Ermittelt die Dauer der Videodatei in Sekunden"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_file
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except:
        return 0

def make_720p(input_file, thread_id):
    output_file = os.path.join("720p", os.path.basename(input_file))
    start_time = time.time()
    total_duration = get_duration(input_file)
    
    try:
        cmd = [
            'ffmpeg',
            '-hide_banner',
            '-i', input_file,
            '-s', 'hd720',
            '-c:v', 'libx265',
            '-crf', '23',
            '-preset', 'fast',
            '-progress', '-',
            '-nostats',
            '-y',  # Überschreiben ohne Nachfrage
            output_file
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 universal_newlines=True, bufsize=1)
        
        for line in process.stdout:
            line = line.strip()
            if 'out_time_ms' in line:
                current_time = float(line.split('=')[1]) / 1000000  # Mikrosekunden zu Sekunden
                progress = current_time / total_duration if total_duration > 0 else 0
                
                with progress_lock:
                    progress_data[thread_id] = {
                        'filename': os.path.basename(input_file),
                        'progress': min(0.99, progress),  # 100% erst bei Abschluss
                        'current': current_time,
                        'total': total_duration,
                        'status': 'running'
                    }
        
        process.wait()
        if process.returncode == 0:
            os.rename(input_file, os.path.join("done", os.path.basename(input_file)))
            with progress_lock:
                progress_data[thread_id]['progress'] = 1.0
                progress_data[thread_id]['status'] = 'done'
            return True, input_file, timedelta(seconds=time.time() - start_time)
        else:
            with progress_lock:
                progress_data[thread_id]['status'] = 'failed'
            return False, input_file, timedelta(seconds=time.time() - start_time), "FFmpeg error"
    
    except Exception as e:
        with progress_lock:
            progress_data[thread_id]['status'] = 'error'
        return False, input_file, timedelta(seconds=time.time() - start_time), str(e)

def draw_progress_bars(total_files, processed_count):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"Video Konvertierung | Dateien: {processed_count}/{total_files}")
    print("=" * TERMINAL_WIDTH)
    
    active_threads = {k: v for k, v in progress_data.items() if v.get('status') in ['running']}
    
    if not active_threads:
        print("Keine aktiven Threads...")
        print("=" * TERMINAL_WIDTH)
        return
    
    max_name_len = max(len(data['filename']) for data in active_threads.values())
    
    for thread_id, data in sorted(active_threads.items()):
        progress = data['progress']
        bar_width = TERMINAL_WIDTH - max_name_len - 30
        filled = int(round(bar_width * progress))
        bar = '#' * filled + '-' * (bar_width - filled)
        
        current_time = str(timedelta(seconds=int(data['current']))).split('.')[0]
        total_time = str(timedelta(seconds=int(data['total']))).split('.')[0] if data['total'] > 0 else '?'
        
        print(f"Thread {thread_id}: {data['filename'].ljust(max_name_len)} "
              f"[{bar}] {progress*100:5.1f}% "
              f"({current_time}/{total_time})")
    
    print("=" * TERMINAL_WIDTH)

def main():
    os.makedirs("720p", exist_ok=True)
    os.makedirs("done", exist_ok=True)

    # FFmpeg Verfügbarkeit prüfen
    if subprocess.run(['ffmpeg', '-version'], capture_output=True).returncode != 0:
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
    
    print(f"Starte Konvertierung von {total_files} Dateien mit {num_workers} Threads...")
    time.sleep(1)

    processed_count = 0
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(make_720p, file, i): i for i, file in enumerate(files_to_process)}
        
        while futures:
            done, _ = concurrent.futures.wait(futures, timeout=UPDATE_INTERVAL)
            draw_progress_bars(total_files, processed_count)
            
            for future in done:
                thread_id = futures[future]
                processed_count += 1
                del futures[thread_id]
                
                try:
                    success, file, duration, *error = future.result()
                    if not success:
                        print(f"Fehler bei {file}: {error[0] if error else 'Unbekannter Fehler'}")
                except Exception as e:
                    print(f"Unerwarteter Fehler: {str(e)}")

    # Finaler Status
    print("\n" + "=" * TERMINAL_WIDTH)
    duration = timedelta(seconds=round(time.time() - start_time))
    print(f"Konvertierung abgeschlossen in {duration}")
    print(f"Erfolgreich verarbeitet: {processed_count}/{total_files}")

if __name__ == "__main__":
    main()