import csv
import subprocess

def run_process_audio(video_path, csv_path, results_path, subject_id):
    subprocess.run([
        'python', 'src/process_audio_v2.py',
        '--video_path', video_path,
        '--csv_path', csv_path,
        '--loglevel', "DEBUG",
        '--results_path', results_path,
        '--subject_id', subject_id
    ])

def main():
    input_csv = 'to_process.csv'  

    with open(input_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            video_path = row['video_path']
            csv_path = row['csv_path']
            results_path = row['results_path']
            subject_id = row['subject_id']

            run_process_audio(video_path, csv_path, results_path, subject_id)

if __name__ == "__main__":
    main()