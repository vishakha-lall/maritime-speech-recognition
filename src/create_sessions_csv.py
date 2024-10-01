import os
import csv
from datetime import datetime

# Define the folder path where the CSV files are located
folder_path = '/run/user/1000/gvfs/smb-share:server=192.168.1.155,share=vmimdata/Vishakha/DE_markers/psam_automation'

# Output CSV file
output_file = '/home/vishakha/Desktop/session_data.csv'

# Initialize variables
start_id = 27
client_id = 2
subject_id = 11

# Create and open the output CSV file for writing
with open(output_file, mode='w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    
    # Write the header row
    csv_writer.writerow(['id', 'date', 'subject_id', 'exercise_id', 'client_id'])
    files = [f for f in os.listdir(folder_path) if f.endswith('.csv') and '-' in f]
    files_sorted = sorted(files, key=lambda x: datetime.strptime(x.split('-')[0], '%Y%m%d'))
    prev_sub = 1
    # Iterate through all files in the specified folder
    for file_name in files_sorted:
        # Only process CSV files with the specified format
        if file_name.endswith('.csv') and '-' in file_name:
            # Extract date and subject_id + exercise_id part from the file name
            date_part, identifier = file_name.split('-')[0], file_name.split('-')[1]
            
            # Convert date to YYYY-MM-DD format
            date_formatted = datetime.strptime(date_part, '%Y%m%d').strftime('%Y-%m-%d')
            
            # Extract the subject id (first two digits) and exercise id (last digit)
            exercise_id = 1 if identifier[2] == 'A' else 2  # Exercise ID: 'A' -> 1, 'B' -> 2
            if prev_sub != int(identifier[:2]):
                subject_id += 1 
            prev_sub = int(identifier[:2])
            # Write row to CSV
            csv_writer.writerow([start_id, date_formatted, subject_id, exercise_id, client_id])
            # Increment ID for the next row
            start_id += 1
