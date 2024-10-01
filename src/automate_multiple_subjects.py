import csv
import subprocess

def run_process_audio(video_path, results_path, session_id):
    subprocess.run([
        'python', 'src/process_audio_v2.py',
        '--video_path', video_path,
        '--loglevel', "DEBUG",
        '--results_path', results_path, 
        '--session_id', session_id
    ])

def main():
    input_csv = 'to_process_psam.csv'  

    with open(input_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            video_path = row['video_path']
            results_path = "/home/vishakha/Documents/speech_processing/PSAM Pilots"
            session_id = row['session_id']

            run_process_audio(video_path, results_path, session_id)

if __name__ == "__main__":
    main()